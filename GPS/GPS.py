
import time
from .decoders import PUBX_datetime_decoder, PUBX_decoder, ubx_checksum, ubx_payload_length

class GPS_PUBX_COMMANDS:
    read_data = "$PUBX,00*33" # returns $PUBX,00,hhmmss.ss,Latitude,N,Longitude,E,AltRef,NavStat,Hacc,Vacc,SOG,COG,Vvel,ageC,HDOP,VDOP,TDOP,GU,RU,DR,*cs<CR><LF>
    read_date = '$PUBX,04*37' # returns $PUBX,04,hhmmss.ss,ddmmyy,UTC_TOW,UTC_WNO,LEAP_SEC,Clk_B,Clk_D,PG,*cs<CR><LF>


    disableRMC = "PUBX,40,RMC,0,0,0,0,0,0" # Minimum location info
    disableGLL = "PUBX,40,GLL,0,0,0,0,0,0" # Geographic position - Latitude/Longitude
    disableGSV = "PUBX,40,GSV,0,0,0,0,0,0" # Satellites in view
    disableGSA = "PUBX,40,GSA,0,0,0,0,0,0" # GPS DOP and active satellites
    disableGGA = "PUBX,40,GGA,0,0,0,0,0,0" # 3D location fix
    disableVTG = "PUBX,40,VTG,0,0,0,0,0,0" # Vector track an Speed over the Ground
    disableZDA = "PUBX,40,ZDA,0,0,0,0,0,0" # Time and Date

    enableRMC = "PUBX,40,RMC,0,1,0,0,0,0" # Minimum location info
    enableGLL = "PUBX,40,GLL,0,1,0,0,0,0" # Geographic position - Latitude/Longitude
    enableGSV = "PUBX,40,GSV,0,1,0,0,0,0" # Satellites in view
    enableGSA = "PUBX,40,GSA,0,1,0,0,0,0" # GPS DOP and active satellites
    enableGGA = "PUBX,40,GGA,0,1,0,0,0,0" # 3D location fix
    enableVTG = "PUBX,40,VTG,0,1,0,0,0,0" # Vector track an Speed over the Ground
    enableZDA = "PUBX,40,ZDA,0,1,0,0,0,0" # Time and Date

    baud9600  = "PUBX,41,1,3,3,9600,0" # 9600 baud
    baud38400 = "PUBX,41,1,3,3,38400,0" # 38400 baud
    baud57600 = "PUBX,41,1,3,3,57600,0" # 57600 baud
    baud115200= "PUBX,41,1,3,3,115200,0" # 115200 baud


class GPS_UBX_COMMANDS:
    gpsPowerOn = [[0x06, 0x04],[0x00, 0x00,0x09, 0x00]] # gps on
    gpsPowerOff = [[0x06, 0x04],[0x00, 0x00,0x09, 0x01]] # gps off - save settings ~5mA
    gpsBackupMode = [[0x02, 0x41],[0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]] # Set GPS to backup mode (sets it to never wake up on its own) <5mA
    gpsRestart = [[0x02, 0x41],[0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00]] # gps restart
    gpsLowPowerMode = [[0x06, 0x11],[0x0]] # gps low power mode
    gpsMaxPerformanceMode = [[0x06, 0x11],[0x1]] # gps max performance mode - always looking for satellites
    gpsEcoMode = [[0x06, 0x11],[0x4]] # gps eco mode - starts as Max Performance Mode until finding satellites then goes to Eco Mode



class GPS_UART:
    def __init__(self, uart, debug=False) -> None:
        self.gps_pubx_commands = GPS_PUBX_COMMANDS()
        self.gps_ubx_commands = GPS_UBX_COMMANDS()
        self._uart = uart
        self.debug = debug
        self.datetime = None
        self.last_read = None

    def _write_command(self, command)->None:
        self._uart.write(command)

    def _readline(self)->str:
        return self._uart.readline()

    def send_pubx_command(self,command)->None:
        self._write_command('$'.encode('ASCII'))
        time.sleep(0.1)
        self._write_command(command.encode('ASCII'))
        time.sleep(0.1)
        self._write_command(b'\r\n')
        time.sleep(0.1)

    def read_gps_data(self,print_data = False)->dict|None:
        self.send_pubx_command(GPS_PUBX_COMMANDS.read_data)
        time.sleep(0.1)

        read = self._read_sentence()
        if read:
            decoded_data = PUBX_decoder(read)
            self.last_read = decoded_data
            if print_data or self.debug:
                print(f'GPS data decoded: {decoded_data}')
            return decoded_data
        return None


    def read_gps_UTC_datetime(self,print_data = False)->dict|None:
        self.send_pubx_command( GPS_PUBX_COMMANDS.read_date)
        time.sleep(0.1)

        read = self._read_sentence()
        if read:
            decoded_data = PUBX_datetime_decoder(read)
            self.datetime = decoded_data
            if print_data or self.debug:
                print(f'GPS datetime decoded: {decoded_data}')
            return decoded_data
        return None

    def _read_sentence(self,print_data = False):
        # Only continue if we have at least 11 bytes in the input buffer
        if self._uart.in_waiting < 11:
            return None

        sentence = self._readline()
        if sentence is None or sentence == b"" or len(sentence) < 1:
            return None
        try:
            sentence = str(sentence, "ascii").strip()
        except UnicodeError:
            return None
        # Look for a checksum and validate it if present.
        if len(sentence) > 7 and sentence[-3] == "*":
            # Get included checksum, then calculate it and compare.
            expected = int(sentence[-2:], 16)
            actual = 0
            for i in range(1, len(sentence) - 3):
                actual ^= ord(sentence[i])
            if actual != expected:
                return None  # Failed to validate checksum.

            # copy the raw sentence
            self._raw_sentence = sentence
            if print_data or self.debug:
                print(f'GPS raw read: {sentence}')
            return sentence
        # At this point we don't have a valid sentence
        return None



    def send_ubx_command(self,class_id:list[hex], payload:list[hex])->None:
        final_command = []
        # set 2 sync chars - 2 bytes [0xB5 0x62]
        final_command.append(0xB5)
        final_command.append(0x62)
        # set class - 1 byte
        final_command.append(class_id[0])
        # set id - 1 byte
        final_command.append(class_id[1])
        # calculate payload length - 2 bytes
        final_command.extend(ubx_payload_length(payload))
        # payload - n bytes
        final_command.extend(payload)
        # checksum - include: class byte, id byte, length 2 bytes, payload n bytes - 2 bytes
        final_command.extend(ubx_checksum(final_command[2:]))
        self._write_command(bytearray(final_command))

    def disable_nmea_output(self)->None:
        self.send_pubx_command(self.gps_pubx_commands.disableRMC) # disable RMC output
        self.send_pubx_command(self.gps_pubx_commands.disableGGA) # disable GGA output
        self.send_pubx_command(self.gps_pubx_commands.disableGSA) # disable GSA output
        self.send_pubx_command(self.gps_pubx_commands.disableGSV) # disable GSV output
        self.send_pubx_command(self.gps_pubx_commands.disableVTG) # disable VTG output
        self.send_pubx_command(self.gps_pubx_commands.disableGLL) # disable GLL output