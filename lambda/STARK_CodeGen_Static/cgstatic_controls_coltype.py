#STARK Code Generator component.
#Produces HTML code for different controls, depending on column type

#Python Standard Library
import base64
import textwrap

def create(data):

    col             = data['col']
    col_type        = data['col_type']
    col_varname     = data['col_varname']
    entity          = data['entity']
    entity_varname  = data['entity_varname']
    html_code       = ""

    if isinstance(col_type, str):
        col_type = col_type.lower()


    if col_type == "date":
        html_code=f"""<b-form-datepicker id="{col_varname}" show-decade-nav v-model="{entity_varname}.{col_varname}" class="mb-2"></b-form-datepicker>"""

    elif col_type == "time":
        html_code=f"""<b-form-timepicker id="{col_varname}" v-model="{entity_varname}.{col_varname}" class="mb-2"></b-form-timepicker>"""

    elif col_type in [ "yes-no", "boolean" ]:
        if col_type == "yes-no":
            checked   ="Yes"
            unchecked ="No"
        elif col_type == "boolean":
            checked   ="True"
            unchecked ="False"

        html_code=f"""<b-form-checkbox id="{col_varname}" v-model="{entity_varname}.{col_varname}" class="mb-2" value="{checked}" unchecked-value="{unchecked}">{{{{ {entity_varname}.{col_varname} }}}}</b-form-checkbox>"""

    elif col_type == "multi-line-string":
        html_code=f"""<b-form-textarea id="{col_varname}" v-model="{entity_varname}.{col_varname}" class="mb-2" rows="4" max-rows="8"></b-form-textarea>"""

    elif isinstance(col_type, list):
        html_code=f"""<select class="form-control" id="{col_varname}" v-model="{entity_varname}.{col_varname}">
                                <option disabled value="">Please select one</option>"""
        for item in col_type:
            html_code+=f"""
                                <option>{item}</option>"""
        html_code+=f"""
                            </select>"""

    elif isinstance(col_type, dict):
        #These are the complex data types that need additional settings as part of their spec
        #   All col_type dicts follow this format:
        #       { "type": "columntype", "type-specific attrib1": "value", "type-specific attrib2": "value" }
        #   Only the "type" index is fixed. All the other indexes may vary depending on the column type specified

        #Spinbutton - useful as a user-friendly int chooser. 
        #   Can also be transformed to a generic string chooser, as long as the internal value is mapped to integers
        #       We should probably handle that as a different col type, though
        if col_type["type"] in [ "int-spinner", "decimal-spinner"]:

            spin_wrap = "wrap"
            spin_min  = 0

            if col_type["type"] == "int-spinner":
                spin_step = 1
                spin_max  = 99
            else:
                spin_step = 0.1
                spin_max  = 10
            
            if int(col_type.get('min', 0)) != 0:
                spin_min = int(col_type.get('min'))

            if int(col_type.get('max', 0)) != 0:
                spin_max = int(col_type.get('max'))

            if float(col_type.get('spin_step', 0)) != 0:
                spin_step = float(col_type.get('spin_step', 0))

            if col_type.get('wrap','') == "no-wrap":
                spin_wrap = ""

            html_code=f"""<b-form-spinbutton class="mb-2" id="{col_varname}" v-model="{entity_varname}.{col_varname}" {spin_wrap} min="{spin_min}" max="{spin_max}" step="{spin_step}">"""


        #Tags input - really user-friendly UX for multiple values in a field (think of the "To:" fields in email)
        #FIXME: This has more capabilities built-in, please add them here too (like validators and the other props)
        elif col_type["type"] == "tags":
            tag_limit = 5

            if int(col_type.get('limit', 0)) != 0:
                tag_limit = int(col_type.get('limit', 0))

            html_code=f"""<b-form-tags input-id="{col_varname}" v-model="{entity_varname}.{col_varname}" :limit="{tag_limit}" remove-on-delete></b-form-tags>"""

        #Rating - nice UI to give a 1-5 (or 1-N) feedback
        elif col_type["type"] == "rating":
            rating_max = 5

            if int(col_type.get('max', 0)) != 0:
                rating_max = int(col_type.get('max', 0))

            html_code=f"""<b-form-rating id="{col_varname}" v-model="{entity_varname}.{col_varname}" stars="{rating_max}" show-value></b-form-rating>"""

        #A group of check boxes for multiple choice inputs
        elif col_type["type"] == "multiple choice":

            values = col_type.get('values', [])

            html_code=f"""<b-form-checkbox-group id="{col_varname}" v-model="{entity_varname}.{col_varname}">"""
            
            for value in values:
                html_code+=f"""<b-form-checkbox value="{value}">{value}</b-form-checkbox>"""
            
            html_code+=f"""</b-form-checkbox-group>"""


        elif col_type["type"] in [ "radio button", "radio bar" ]:

            values  = col_type.get('values', [])
            buttons = ""
            if col_type["type"] == "radio bar":
                buttons = 'buttons button-variant="outline-secondary"'

            html_code=f"""<b-form-radio-group id="{col_varname}" v-model="{entity_varname}.{col_varname}" {buttons}>"""
            
            for value in values:
                html_code+=f"""<b-form-radio value="{value}">{value}</b-form-radio>"""
            
            html_code+=f"""</b-form-radio-group>"""



    else:
        html_code=f"""<input type="text" class="form-control" id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">"""


                      

    return html_code