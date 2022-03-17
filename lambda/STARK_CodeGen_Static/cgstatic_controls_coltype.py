#STARK Code Generator component.
#Produces HTML code for different controls, depending on column type

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter

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

    elif col_type == "number":
        html_code=f"""<input type="number" class="form-control" id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">"""

    elif col_type == "int":
        html_code=f"""<input type="number"  min="0" step="1" class="form-control" id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">"""

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
        html_code=f"""<b-form-select id="{col_varname}" v-model="{entity_varname}.{col_varname}" :options="lists.{col_varname}">
                                <template v-slot:first>
                                    <b-form-select-option :value="null" disabled>-- Please select an option --</b-form-select-option>
                                </template>
                            </b-form-select>"""

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
            attribs_for_tags_list = ''
            datalist_helper = ''

            if int(col_type.get('limit', 0)) != 0:
                tag_limit = int(col_type.get('limit', 0))
            if col_type.get('values','') != '':
                #Do not include validator for now, that's for later sprint
                #attribs_for_tags_list = f""":input-attrs="{{ list: '{col_varname}-tags-list', autocomplete: 'off' }}" :tag-validator="validate_{entity_varname}" add-on-change"""
                attribs_for_tags_list = f""":input-attrs="{{ list: '{col_varname}-tags-list', autocomplete: 'off' }}" add-on-change"""
                datalist_helper = f"""<b-form-datalist id="{col_varname}-tags-list" :options="lists.{col_varname}"></b-form-datalist>"""

            html_code=f"""<b-form-tags input-id="{col_varname}" v-model="{entity_varname}.{col_varname}" :limit="{tag_limit}" remove-on-delete {attribs_for_tags_list}></b-form-tags>"""

            if datalist_helper != '':
                html_code+=f"""
                            {datalist_helper}"""
            #FIXME: Eventually (later sprint) we may have to make datalist helper creation more generic (reusable by most other control types)

        #Rating - nice UI to give a 1-5 (or 1-N) feedback
        elif col_type["type"] == "rating":
            rating_max = 5

            if int(col_type.get('max', 0)) != 0:
                rating_max = int(col_type.get('max', 0))

            html_code=f"""<b-form-rating id="{col_varname}" v-model="{entity_varname}.{col_varname}" stars="{rating_max}" show-value></b-form-rating>"""

        #A group of check boxes for multiple choice inputs
        elif col_type["type"] == "multiple choice":

            values = col_type.get('values', [])

            html_code=f"""<b-form-checkbox-group id="{col_varname}" v-model="{entity_varname}.{col_varname}" :options="lists.{col_varname}"></b-form-checkbox-group>"""

        elif col_type["type"] in [ "radio button", "radio bar" ]:

            values  = col_type.get('values', [])
            buttons = ""

            #FIXME: no ugly hack needed once we use BootstrapVue b-form-group instead of basic Bootstrap form groups
            ugly_hack = "" #need for now to force radio bar to render under the label like the others, instead of beside the label
            if col_type["type"] == "radio bar":
                buttons = 'buttons button-variant="outline-secondary"'
                ugly_hack = "<br>"

            html_code=f"""{ugly_hack}<b-form-radio-group id="{col_varname}" v-model="{entity_varname}.{col_varname}" :options="lists.{col_varname}" {buttons}></b-form-radio-group>"""

        elif col_type["type"] == "relationship":
            has_one = col_type.get('has_one', '')

            if  has_one != '':
                #simple 1-1 relationship
                foreign_entity  = converter.convert_to_system_name(has_one)

                html_code=f"""<b-form-select id="{col_varname}" v-model="{entity_varname}.{col_varname}" :options="lists.{col_varname}" onmouseover="root.list_{foreign_entity}()" onfocus="root.list_{foreign_entity}()">
                                <template v-slot:first>
                                    <b-form-select-option :value="null" disabled>-- Please select an option --</b-form-select-option>
                                </template>
                            </b-form-select>"""

    else:
        html_code=f"""<input type="text" class="form-control" id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">"""


                      

    return html_code


def create_list(data):

    col         = data['col']
    col_type    = data['col_type']
    col_varname = data['col_varname']
    js_code     = ""
    listable    = False

    if isinstance(col_type, str):
        col_type = col_type.lower()

    #We only make lists for specific column types and just return immediately for anything else
    if isinstance(col_type, list) or ( 
        isinstance(col_type, dict) and col_type["type"] in [ "multiple choice", "radio button", "radio bar"] 
    ) or ( 
        isinstance(col_type, dict) and col_type["type"] == "relationship" and col_type.get('has_one','') != ''
    ) or (
        isinstance(col_type, dict) and col_type["type"] == "tags" and col_type.get('values','') != '' 
    ):
        listable = True

    if not listable: 
        return None

    ##############
    #Our list begins with a declaration of the list, based on the column's variable name
    js_code += f"""'{col_varname}': ["""

    if isinstance(col_type, list):
        for item in col_type:
            js_code += f"""
                        {{ value: '{item}', text: '{item}' }},"""

    elif isinstance(col_type, dict):
        items = col_type.get('values', [])

        for item in items:
            js_code += f"""
                        {{ value: '{item}', text: '{item}' }},"""


    #############
    #Close the list to end
    js_code += f"""
                    ],"""

    return js_code