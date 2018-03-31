import serial

'''
class serialtalker

component          function

command_dic        a dictionary of all the command names 
                   and command codes

confirmation_dic   a dictionary of all the confirmation 
                   codes and confirmation meanings
                   
current_pageid     the index of the current page is storing
                   the latest-registered finger figure 
                   module
                   
hs_response         the current response in hex-like string

__init__()         init the serial, including find the 
                   address of the usb, and setting some 
                   parameters
                   
send()             send a command in binary code
                   by generating a check code and then 
                   packaging them, then receive a respond
                   automatically
                   return:
                    0:  succeed
                   -1:  no response
                   -2:  package damaged
                    1:  responded a error

generate_check()   generate the 2 bytes check code by sum
                   calculation

package()          translate the command into packaged 
                   hex-like string
                   
receive()          receive the response and translate to
                   natural-language phrase from binary code
                   return:
                    0:  succeed
                   -1:  no response
                   -2:  package damaged
                    1:  responded a error

check()            check if the response is correctly 
                   received 

unpack()           translate from a packed binary code sent
                   by finger module into hex string
                   
show_command()     print all commands that are able to send
                   
'''


class SerialTalker(serial.Serial):

    def __init__(self, _port='/dev/ttyUSB0', _baudrate=115200):
        super(SerialTalker, self).__init__(
            port=_port,
            baudrate=_baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        self.current_pageid = -1
        self.hs_response = ''


    # Command Dictionary:
    #  CommandName:
    #     [CommandCode, ByteLengthOfResponse]
    command_dic = {
        'PS_GetImage': ['01', 12],
        'PS_GenChar': ['02', 12],
        'PS_Match': ['03', 14],
        'PS_Search': ['04', 16],
        'PS_RegModel': ['05', 12],
        'PS_StoreChar': ['06', 12],
        'PS_Identify': ['11', 16]
    }

    # Confirmation Dictionary:
    #  ConfirmationCode: MeaningOfResponse
    confirmation_dic = {
        '00': 'succeed',
        '01': 'receiving error',
        '02': 'no fingers on the screen',
        '03': 'failed registering the finger image',
        '06': 'failed generating the figure for a mess finger image',
        '07': 'failed generating the figure for few of figure points',
        '08': 'finger not matching',
        '09': 'finger not found',
        '0a': 'failed merging the figures',
        '0b': 'the address flow over the range of finger base when '
              'accessing',
        '18': 'failed when reading or writing the flash'
    }

    def send(self, command, n_bufferid=-1):
        cmd_item = self.command_dic.get(command)
        s_cmd = cmd_item[0]
        if s_cmd != '':
            print('send: ', s_cmd)
            s_package = self.package(s_cmd, n_bufferid)
            print(s_package)
            s_package =  s_package.replace(' ', '')
            bs_package = bytearray.fromhex(s_package)
            self.write(bs_package)
        else:
            print('there is no such command, please choose'
                  ' one from what is following:')
            self.show_command()
        return self.receive(cmd_item[1])

    def receive(self, bytelength):
        bs_response = self.read(bytelength)
        hs_response = self.unpack(bs_response)
        if hs_response == '':
            print('no response, '
                  'please check the package and send again.')
            return -1
        elif not self.check(hs_response):
            print('package damaged, '
                  'please try to send command again.')
            return -2
        else:
            pass
        print('response: ', hs_response)
        s_confirmation = hs_response[18:20].lower()
        s_response = self.confirmation_dic.get(s_confirmation)
        print(s_response)
        if s_confirmation == '00':
            return 0
        else:
            return 1


    # n_bufferid are supposed to be 1 or 2 if needed
    def package(self, s_command, n_bufferid=1):
        s_package = 'EF01 FFFFFFFF 01'
        if s_command == '01':
            s_package += ' 0003 {} 0005'.format(s_command)
        elif s_command == '02':
            s_package += ' 0004 {} {:02}'\
                .format(s_command, n_bufferid)
            s_package += self.generate_check(s_package)
        elif s_command == '03':
            s_package += ' 0003 {} 0007'.format(s_command)
        #has not been checked if the package code is correct
        elif s_command == '04':
            s_package += ' 0008 {} {:02} 0000 FFFF'\
                .format(s_command, n_bufferid)
            s_package += self.generate_check(s_package)
        elif s_command == '05':
            s_package += ' 0003 {} 0009'.format(s_command)
        elif s_command == '06':
            if self.current_pageid < 10:
                #the used page should less than 10 for simplifying code
                self.current_pageid += 1
                s_package += ' 0006 {} {:02} {:04}'\
                    .format(s_command, n_bufferid, self.current_pageid)
                s_package += self.generate_check(s_package)
            else:
                print('too much finger registered,'
                      ' please clear registered fingers')
        elif s_command == '11':
            s_package += ' 0003 {} 0015'.format(s_command)
        else:
            print('no such command code.')
        return s_package

    # generate a 2 bytes code from summing every byte of
    # the package string from 12th bit to the end
    # to simplify the calculation, we just add every single
    # hex bit (like 0 to f) from 12th to the end
    def generate_check(self, s_package):
        s_package = s_package.replace(' ', '')
        print(s_package)
        s_checking = s_package[12:]
        bytes_checking = []
        while s_checking != '':
            bytes_checking.append(s_checking[0:2])
            s_checking = s_checking[2:]
        print(bytes_checking)
        dec_check = 0
        for byte in bytes_checking:
            # convert byte(hex) into a dec int and add
            dec_check += int(byte, base=16)
        s_check = ' {0:04X}'.format(dec_check)
        return s_check

    def unpack(self, bs_response):
        self.hs_response = bs_response.hex()
        return self.hs_response

    def check(self, s_response):
        s_checking = s_response[12:-4]
        bytes_checking = []
        while s_checking != '':
            bytes_checking.append(s_checking[0:2])
            s_checking = s_checking[2:]
        dec_check = 0
        for byte in bytes_checking:
            # convert byte(hex) into a dec int and add
            dec_check += int(byte, base=16)
        if dec_check == int(s_response[-4:], base=16):
            return True
        else:
            return False

    def show_command(self):
        for cmd_key in self.command_dic.keys():
                print(cmd_key)


