#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap
import os

#Private modules
import cgstatic_relationships as cg_rel
import cgstatic_html_generic_header as cg_header
import cgstatic_html_generic_footer as cg_footer
import cgstatic_html_generic_bodyhead as cg_bodyhead
import cgstatic_html_generic_loadingmodal as cg_loadmod
import convert_friendly_to_system as converter

def create(data):

    #project = data["Project Name"]
    entity  = data["Entity"]
    cols    = data["Columns"]
    pk      = data["PK"]
    bucket_name = data['Bucket Name'] #temporary: remove once s3 credentials for file upload is solved
    region_name   = os.environ['AWS_REGION'] #temporary: remove once s3 credentials for file upload is solved

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname     = converter.convert_to_system_name(pk)

    source_code  = cg_header.create(data)
    source_code += cg_bodyhead.create(data, "Delete")

    source_code += f"""\
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
        print(col)
        print(col_type)
        # if isinstance(col_type, dict):
        #     if col_type["type"] == "relationship":
        #         has_many = col_type.get('has_many', '')
        #         foreign_entity  = converter.convert_to_system_name(has_many)
        #         print(foreign_entity)
            # foreign_entity  = converter.convert_to_system_name(has_many)
            # if has_many != '':
            #     source_code += f"""
            #     <div class="form-group row">
            #         <label for="{foreign_entity}" class="col-sm-2 col-form-label">{foreign_entity}</label>
            #         <div class="col-sm-10">
            #             <b-form-group label-for="tags-with-dropdown">
            #                 <b-form-tags id="tags-with-dropdown" v-model="multi_select_values.{foreign_entity}" no-outer-focus class="mb-2">
            #                     <template v-slot="{{ tags, disabled, addTag, removeTag }}">
            #                         <ul v-if="tags.length > 0" class="list-inline d-inline-block mb-2">
            #                             <li v-for="tag in tags" :key="tag" class="list-inline-item">
            #                                 <b-form-tag 
            #                                     @remove="removeTag(tag)" 
            #                                     :title="tag" 
            #                                     :disabled="true" 
            #                                     variant="info" >
            #                                     {{ tag_display_text(tag) }}
            #                                 </b-form-tag>
            #                             </li>
            #                         </ul>
            #                     </template>
            #                 </b-form-tags>
            #             </b-form-group>
            #         </div>
            #     </div>
            #     """



    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                            <div class="form-group row">
                                <label for="{col_varname}" class="col-sm-2 col-form-label">{col}</label>
                                <div class="col-sm-10">"""
        if col_type == 'file-upload':
            source_code += f""" 
                            <a :href="'https://{bucket_name}.s3.{region_name}.amazonaws.com/uploaded_files/' + {entity_varname}.STARK_uploaded_s3_keys.{col_varname}">
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