import os
import sys
import time
import subprocess


def generate_heat_commands(template_path, image_name, stack_name):
    if 'http' in template_path:
        heat_url_start_command = 'heat stack-create --template-url %s -P image_name=%s  %s' \
            % (template_path, image_name, stack_name)
        return heat_url_start_command
    else:
        heat_file_start_command = 'heat stack-create -f %s -P image_name=%s  %s' \
            % (template_path, image_name, stack_name)
        print heat_file_start_command
        return heat_file_start_command


def launch_stack_commands(template_path, image_name, stack_name):
    heat_command = generate_heat_commands(
        template_path, image_name, stack_name)
    print 'Heat command: %s' % heat_command

    heat_command_echo_info = _operate_heat_command(heat_command)
    print 'create stack in process, pls wait'

    judge_command_echo = os.popen('echo $?').read()
    if str(judge_command_echo) != '0':
        #raise Exception('heat command error, pls check it and try again!')
        pass
    if 'error' in heat_command_echo_info or 'ERROR' in heat_command_echo_info:
        raise Exception(heat_command_echo_info)

    _check_stack_status(stack_action='stack-create', delete_stack_name=None)


def delete_stack(stack_name):
    heat_command_check_info = _operate_heat_command('heat stack-list')
    if stack_name in heat_command_check_info:
        delete_heat_stack = 'heat stack-delete %s' % stack_name
        heat_command_echo_info = _operate_heat_command(delete_heat_stack)
        print 'delete stack in process, pls wait'
        print heat_command_echo_info
        if 'error' in heat_command_echo_info or 'ERROR' in heat_command_echo_info:
            raise Exception(heat_command_echo_info)
        _check_stack_status(
            stack_action='stack-delete', delete_stack_name=stack_name)
    else:
        pass


def _operate_heat_command(heat_command):
    heat_command_echo = subprocess.Popen(
        heat_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    heat_command_echo_info = heat_command_echo.stdout.read()
    heat_command_echo.wait()
    return heat_command_echo_info


def _check_stack_status(stack_action, delete_stack_name):
    heat_status_command = 'heat stack-list'
    for i in range(180):
        time.sleep(5)
        heat_status_command_echo = subprocess.Popen(
            heat_status_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        heat_status_command_echo_info = heat_status_command_echo.stdout.read()
        heat_status_command_echo.wait()

        if 'CREATE_FAILED' in heat_status_command_echo_info:
            raise Exception('heat create stack failed!')
        elif 'ROLLBACK_IN_PROGRESS' in heat_status_command_echo_info:
            raise Exception('Create failed and rollback in progress')
        elif i == 179:
            raise Exception('heat create stack timeout!')

        if stack_action == 'stack-create':
            if 'CREATE_IN_PROGRESS' in heat_status_command_echo_info:
                print 'create stack in process, pls wait'
            elif 'CREATE_FAILED' not in heat_status_command_echo_info and 'CREATE_IN_PROGRESS' not in heat_status_command_echo_info:
                print 'create stack success!'
                break
        elif stack_action == 'stack-delete':
            if 'DELETE_IN_PROGRESS' in heat_status_command_echo_info:
                print 'delete stack in process, pls wait'
            elif delete_stack_name not in heat_status_command_echo_info:
                print 'delete stack success!'
                break

if __name__ == '__main__':

    openstack_env = 'openenv_admin.sh'
    if os.path.exists(openstack_env):
        env_command = 'source ' + os.getcwd() + '/' + openstack_env
        os.system(env_command)
    else:
        print 'if environment variables are not set pls assign a env file, else ignore this item'

    if sys.argv[1].lower() == 'stack-create':
        if len(sys.argv) < 5:
            raise Exception('python argv number error')
        else:
            template_path = sys.argv[2]
            image_name = sys.argv[3]
            stack_name = sys.argv[4]
            launch_stack_commands(template_path, image_name, stack_name)

    elif sys.argv[1].lower() == 'stack-delete':
        if len(sys.argv) < 3:
            raise Exception('python argv number error')
        else:
            stack_name = sys.argv[2]
            delete_stack(stack_name)
    else:
        raise Exception(
            'command error, if use "stack-create" need three parameters, else "stack-abandon" need two parameters')
