#This takes a user-supplied human-friendly name and converts that to the appropriate 
#   system-friendly name (e.g., variable name, CF stack name, or S3 bucket name)


def convert_to_system_name(friendly_name, target='variable'):

    preprocessed_name = friendly_name.replace(" ", "_")

    if target == "s3":
        system_name = to_s3(preprocessed_name)
    elif target == 'cf-stack':
        system_name = to_cloudformation_stack(preprocessed_name)
    elif target == 'cf-resource':
        system_name = to_cloudformation_logicalname(preprocessed_name)
    else:
        system_name = to_variable(preprocessed_name)

    return system_name




def to_variable(name):
    system_name = ''
    whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789'

    for char in name:
        if char in whitelist:
            system_name += char
    #This also works, if rather obtuse and uses a magic method
    #system_name = ''.join(filter(whitelist.__contains__, name))

    #Must begin with letter or underscore, else prepend underscore
    if system_name[0] in '0123456789':
        system_name = '_' + system_name

    return system_name


def to_s3(name):
    system_name = ''
    whitelist = 'abcdefghijklmnopqrstuvwxyz-.0123456789'

    name = name.lower()
    for char in name:
        if char in whitelist:
            system_name += char

    #Must start with letter or number, else prepend 's'
    if system_name[0] in "-.":
        system_name = 's' + system_name

    #Follow S3 name length rules
    if len(system_name) < 3:
        system_name += "_stark"
    elif len(system_name) > 63:
        system_name = system_name[0:63]

    return system_name



def to_cloudformation_stack(name):
    system_name = ''
    whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-0123456789'

    for char in name:
        if char in whitelist:
            system_name += char

    #Must start with a letter, else prepend 's'
    if system_name[0] in "-0123456789":
        system_name = 's' + system_name

    #Follow CF stack name length rules
    if len(system_name) > 128:
        system_name - system_name[0:128]

    return system_name

def to_cloudformation_logicalname(name):
    system_name = ''
    whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

    for char in name:
        if char in whitelist:
            system_name += char

    return system_name

