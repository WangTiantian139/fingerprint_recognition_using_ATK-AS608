import serialtalker
import time

talker = serialtalker.SerialTalker(
    _port='/dev/ttyUSB0',
    _baudrate=115200,
)

print(talker.name, talker.isOpen())
print()

user_dic = {}

print('use send(command) to send a command.')
print('command list are listed as following:')
talker.show_command()
print()

print('use add_user(name) or identify() to add '
      'a finger module or identify.\n')


def add_user(name):

    while True:

        get_image_times = 0

        while get_image_times < 2:

            get_img_flag, gen_char_flag = 999, 999

            while get_img_flag:

                time.sleep(2.0)
                get_img_flag = \
                    talker.send('PS_GetImage')

                if get_img_flag == 0:
                    print('succeed to register a finger image.')
                    time.sleep(2.0)
                    gen_char_flag = \
                        talker.send('PS_GenChar',
                                    n_bufferid=get_image_times+1)
                    if gen_char_flag == 0:
                        print('succeed to generate a character.')
                        get_image_times = get_image_times + 1
                    elif gen_char_flag in [1, -1, -2]:
                        get_img_flag = 999
                    else:
                        print('unknown error')
                        quit()

                elif get_img_flag in [1, -1, -2]:
                    get_img_flag = 999
                else:
                    print('unknown error')
                    quit()

        # register the finger module
        fng_mod_flag = 999
        while fng_mod_flag:
            time.sleep(2.0)
            fng_mod_flag = \
                talker.send('PS_RegModel')
            if fng_mod_flag == 0:
                print('succeed to register the finger module.')
            elif fng_mod_flag in [-1, -2]:
                print(fng_mod_flag)
            else:
                break
        if fng_mod_flag == 1:
            continue
        else:
            pass

        # store the finger module
        str_fng_flag = 999
        while str_fng_flag:
            time.sleep(2.0)
            str_fng_flag = \
                talker.send('PS_StoreChar', n_bufferid=2)
            if str_fng_flag == 0:
                page_id = talker.current_pageid
                user_dic[page_id] = name
                print('succeed to store the finger module '
                      'at page {}'.format(page_id))
            elif str_fng_flag in [-1, -2]:
                print(str_fng_flag)
            else:
                break
        if str_fng_flag == 1:
            continue
        else:
            break


def identify():
    time.sleep(2.0)
    sch_flag = talker.send('PS_Identify')
    if sch_flag == 0:
        response = talker.hs_response
        print('the response is:\n', response)
        page_id = int(response[20:24],base=16)
        score = response[24:28]
        name = is_id_exist(page_id)
        print('you are {}, at page {}, whose score is {}' \
              .format(name, page_id, score))
    else:
        print(sch_flag)


def is_name_exist(name):
    if name in user_dic.values():
        print('the user is exist')
    else:
        print('no such user.')


def is_id_exist(page_id):
    name = user_dic.get(page_id, -1)
    if name == -1:
        print('this user has not registered.')
        name = input('please type a name for the user: ')
        user_dic[page_id] = name
        print('this user has been registered automatically')
        print()
    else:
        pass
    return name
