#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
from asyncio import constants
import base64
import textwrap
import os
import importlib

#Private modules
prepend_dir = ""
if 'libstark' in os.listdir():
    prepend_dir = "libstark.STARK_CodeGen_Static."

cg_header   = importlib.import_module(f"{prepend_dir}cgstatic_html_generic_header")
cg_footer   = importlib.import_module(f"{prepend_dir}cgstatic_html_generic_footer")
cg_bodyhead = importlib.import_module(f"{prepend_dir}cgstatic_html_generic_bodyhead")
cg_loadmod  = importlib.import_module(f"{prepend_dir}cgstatic_html_generic_loadingmodal")

import convert_friendly_to_system as converter

def create(data):

    #project = data["Project Name"]
    entity  = data["Entity"]
    cols    = data["Columns"]
    pk      = data["PK"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname     = converter.convert_to_system_name(pk)

    source_code  = cg_header.create(data, "Delete")
    source_code += cg_bodyhead.create(data, "Delete")

    source_code += f"""\
        
        <!--<div class="container-unauthorized" v-if="!stark_permissions['{entity}|Delete']">UNAUTHORIZED!</div>
        <div class="main-continer" v-if="stark_permissions['{entity}|Delete']"> -->
            <div class="container hidden" :style="{{visibility: visibility}}">
                <div class="row">
                    <div class="col">
                        <div class="my-auto">
                            <form class="border p-3">
                            <input type="hidden" id="orig_{pk_varname}" v-model="{entity_varname}.{pk_varname}">
                            <div class="form-group row">
                                <label for="{pk_varname}" class="col-sm-2 col-form-label">{pk}</label>
                                <div class="col-sm-10">
                                    <input type="text" class="form-control-plaintext" readonly id="{pk_varname}" placeholder="" v-model="{entity_varname}.{pk_varname}">
                                </div>
                            </div>"""
    
            



    for col, col_type in cols.items():
        # print(col_type)
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                            <div class="form-group row">
                                <label for="{col_varname}" class="col-sm-2 col-form-label">{col}</label>
                                <div class="col-sm-10">"""
        if isinstance(col_type, dict):
            if col_type["type"] == "relationship":
                has_one = col_type.get('has_one', '')
                has_many = col_type.get('has_many', '')

                if  has_one != '':
                #simple 1-1 relationship
                    foreign_entity  = converter.convert_to_system_name(has_one)
                    source_code += f"""
                    <input type="text" class="form-control-plaintext" readonly id="{foreign_entity}" placeholder="" v-model="{entity_varname}.{foreign_entity}">
                    """
                    
                if  has_many != '':
                # 1-M relationship
                    foreign_entity  = converter.convert_to_system_name(has_many)
                    print(foreign_entity)
                    source_code += f"""
                    <b-form-group label-for="tags-with-dropdown">
                        <b-form-tags id="tags-with-dropdown" v-model="multi_select_values.{foreign_entity}" no-outer-focus class="mb-2">
                            <template v-slot="{{ tags, disabled, addTag, removeTag }}">
                                <ul v-if="tags.length > 0" class="list-inline d-inline-block mb-2">
                                    <li v-for="tag in tags" :key="tag" class="list-inline-item">
                                        <b-form-tag 
                                            @remove="removeTag(tag)" 
                                            :title="tag" 
                                            :disabled="true" 
                                            variant="info" >
                                            {{{{ tag_display_text(tag) }}}}
                                        </b-form-tag>
                                    </li>
                                </ul>
                            </template>
                        </b-form-tags>
                    </b-form-group>
                    """
            elif col_type["type"] == 'file-upload':
                source_code += f""" 
                                <a :href="'https://'+ root.object_url_prefix + {entity_varname}.STARK_uploaded_s3_keys.{col_varname}">
                                    <span class="form-control-link" readonly id="{col_varname}" placeholder="" >{{{{{entity_varname}.{col_varname}}}}}</span>   
                                </a>
                                """      
        else:
            source_code += f"""
                            <input type="text" class="form-control-plaintext" readonly id="{col_varname}" placeholder="" v-model="{entity_varname}.{col_varname}">
                            """
        source_code+= f"""</div>
                            </div>"""
    

    source_code += f"""
                            <button type="button" class="btn btn-secondary" onClick="window.location.href='{entity_varname}.html'">Back</button>
                            <button type="button" class="btn btn-danger float-right" onClick="root.delete()">Delete</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""

    source_code += cg_loadmod.create()
    source_code += cg_footer.create()

    return textwrap.dedent(source_code)