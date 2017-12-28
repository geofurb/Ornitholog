from cmd_interface import Commander

if __name__ == '__main__' :
    import os
    os.chdir('..')
    comthread = Commander()
    print('Starting terminal...')
    comthread.start()
    print('Terminal interface started.\n')