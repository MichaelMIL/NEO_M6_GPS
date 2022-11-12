def DMS2DD(value:str,type:str)->float:
    '''
    latitude format ddmm.mmmm, types: N, S
    longitude format dddmm.mmmm, types: E, W
    Returns 2 decimal points
    '''
    #print(f'DMS2DD: {value} {type}')
    if type == 'N' or type == 'S':
        deg = int(value[:2])
        dec = float(value[2:])/60
        if type == 'S':
            return -(deg+dec)
        return(deg+dec)

    if type == 'W' or type == 'E':
        deg = int(value[:3])
        dec = float(value[3:])/60
        if type == 'W':
            return -(deg+dec)
        return(deg+dec)

def PUBX_time_decoder(data:str)->str:
    # hh:mm:ss.ss
    data = data.replace('.','')
    return f'{data[:2]}:{data[2:4]}:{data[4:6]}.{data[6:]}'

def PUBX_decoder(data:str)->dict:
    output = {}
    data_list = data.split(',')
    if data_list[0] == '$PUBX' and data_list[1] == '00':
        output['UTCtime'] = PUBX_time_decoder(data_list[2]) # UTC timestamp
        output['latitude'] = DMS2DD(data_list[3],data_list[4])  # latitude dd
        output['longitude'] = DMS2DD(data_list[5],data_list[6]) # longitude dd
        output['altitude'] = data_list[7] # altitude in meters
        output['mode'] = data_list[8]  # navigation status  
        output['horizontalAccuracy'] = data_list[9] # horizontal accuracy in meters
        output['verticalAccuracy'] = data_list[10] # vertical accuracy in meters
        output['speedOverGround'] = data_list[11] # speed over ground in knots/h
        output['courseOverGround'] = data_list[12] # course over ground in degrees
        output['verticalVelocity'] = data_list[13] # vertical velocity in m/s
        output['ageOfData'] = data_list[14] # age of data in seconds
        output['HDOP'] = data_list[15] # HDOP
        output['VDOP'] = data_list[16] # VDOP
        output['TDOP'] = data_list[17] # TDOP
        output['GPSUnit'] = data_list[18] # GPS unit
        output['GLONASSUnit'] = data_list[19] # GLONASS unit
        output['DRUnit'] = data_list[20].strip() # DR unit
    return output



def PUBX_datetime_decoder(data:str)->str:
    '$PUBX,04,095510.00,200622,122110.00,2215,18,-340309,-2871.946,21*20'
    # DD:MM:YY hh:mm:ss.ss
    #print(f'pubx datetime: {data}')
    data_list = data.split(',')
    if data_list[0] == '$PUBX' and data_list[1] == '04':
        return f'{data[3][:2]}/{data[3][2:4]}/{data[3][4:6]} {PUBX_time_decoder(data[2])}'


def ubx_payload_length(payload:list[int])->list[int]:
    output = [0x0,0x0]
    if len(payload) > 255:
        output[0] = 0xFF
        output[1] = len(payload)-255
    else:
        output[0] = len(payload)
    return output

def ubx_checksum(ubx_command:list[int])->list[int]:
    CK_A,CK_B = 0, 0
    for i in range(len(ubx_command)):
      CK_A = CK_A + ubx_command[i]
      CK_B = CK_B + CK_A

    # ensure unsigned byte range
    CK_A = CK_A & 0xFF
    CK_B = CK_B & 0xFF
    return [CK_A,CK_B]