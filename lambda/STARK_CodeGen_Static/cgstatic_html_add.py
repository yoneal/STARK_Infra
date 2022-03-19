#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import cgstatic_relationships as cg_rel
import cgstatic_controls_coltype as cg_coltype
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

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname     = converter.convert_to_system_name(pk)

    source_code  = cg_header.create(data)
    source_code += cg_bodyhead.create(data, "New")

    source_code += f"""\
            <div class="container hidden" :style="{{visibility: visibility}}">
                <div class="row">
                    <div class="col">
                        <div class="my-auto">
                            <form class="border p-3">
                            <input type="hidden" id="orig_{pk_varname}" v-model="{entity_varname}.{pk_varname}">
                            <div class="form-group">
                                <label for="{pk_varname}">{pk}</label>
                                <input type="text" class="form-control" id="{pk_varname}" placeholder="" v-model="{entity_varname}.{pk_varname}">
                            </div>"""

    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        html_control_code = cg_coltype.create({
            "col": col,
            "col_type": col_type,
            "col_varname": col_varname,
            "entity" : entity,
            "entity_varname": entity_varname
        })

        source_code += f"""
                            <div class="form-group">
                                <label for="{col_varname}">{col}</label>
                                {html_control_code}
                            </div>"""

    source_code += f"""
                            <button type="button" class="btn btn-secondary" onClick="window.location.href='{entity_varname}.html'">Back</button>
                            <button type="button" class="btn btn-primary float-right" onClick="root.add()">Add</button>
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