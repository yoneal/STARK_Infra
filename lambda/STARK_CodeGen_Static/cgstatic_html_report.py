#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import base64
import textwrap

#Private modules
import convert_friendly_to_system as converter
import cgstatic_html_generic_header as cg_header
import cgstatic_html_generic_footer as cg_footer
import cgstatic_html_generic_bodyhead as cg_bodyhead
import cgstatic_html_generic_loadingmodal as cg_loadmod
import cgstatic_html_generic_loadingspinner as cg_loadspin
import cgstatic_controls_coltype as cg_coltype

def create(data):

    project = data["Project Name"]
    entity  = data["Entity"]
    cols    = data["Columns"]
    pk      = data["PK"]

    #Convert human-friendly names to variable-friendly names
    entity_varname = converter.convert_to_system_name(entity)
    pk_varname = converter.convert_to_system_name(pk)

    source_code  = cg_header.create(data, "Report")
    source_code += cg_bodyhead.create(data, "Report")

    source_code += f"""\
            <div class="container" v-if="!showReport">
                <div class="row">
                    <div class="col">
                        <div class="my-auto">
                            <form class="border p-3">
                                <div>
                                    <table class="table table-bordered">
                                                
                                            <div class="alert alert-danger alert-dismissible fade show" v-if="showError">
                                                <strong>Error!</strong> Put operator/s on:
                                                <template v-for="column in no_operator" id="no_operator">
                                                    <tr scope="col"> - {{{{ column }}}}</tr>
                                                </template>
                                            </div>
                                    </table>
                                </div>
                                <table class="table table-bordered">
                                    <tr>
                                        <th style="padding: 10px">
                                            Show Column<br>
                                            <a href="#" style="font-size: 11px" onClick="root.checkUncheck(true)">Check All</a><br>
                                            <a href="#" style="font-size: 11px" onClick="root.checkUncheck(false)">Uncheck All</a>
                                        </th>
                                        <th style="padding: 10px; min-width: 250px"> Field Name </th>
                                        <th style="padding: 10px"> Operator </th>
                                        <th style="padding: 10px"> Filter Value </th>
                                    </tr>
                                    <tr>
                                        <td>
                                             <input type="checkbox" name="check_checkbox" value="{pk_varname}" id="{pk_varname}" v-model="checked_fields">
                                        </td>
                                        <td>
                                                <label for="{pk_varname}">{pk}</label>
                                        </td>
                                        <td>
                                            <b-form-select id="{pk_varname}_operator" :options="lists.Report_Operator" v-model="custom_report.{pk_varname}.operator">
                                                <template v-slot:first>
                                                    <b-form-select-option :value="null" disabled>-- Please select an option --</b-form-select-option>
                                                </template>
                                            </b-form-select>
                                        </td>
                                        <td>
                                            <input type="text" class="form-control" id="{pk_varname}_filter_value" placeholder="" v-model="custom_report.{pk_varname}.value">
                                        </td>
                                    </tr>"""
    


    for col, col_type in cols.items():
        col_varname = converter.convert_to_system_name(col)
        source_code += f"""
                                    <tr>
                                        <td>
                                             <input type="checkbox" name="check_checkbox" value="{col_varname}" id="{col_varname}" v-model="checked_fields">
                                        </td>
                                        <td>
                                                <label for="{col_varname}">{col}</label>
                                        </td>
                                        <td>
                                            <b-form-select id="{col_varname}_operator" :options="lists.Report_Operator" v-model="custom_report.{col_varname}.operator">
                                                <template v-slot:first>
                                                    <b-form-select-option :value="null" disabled>-- Please select an option --</b-form-select-option>
                                                </template>
                                            </b-form-select>
                                        </td>
                                        <td>
                                            <input type="text" class="form-control" id="{col_varname}_filter_value" placeholder="" v-model="custom_report.{col_varname}.value">
                                        </td>
                                    </tr>"""

    source_code += f"""
                                </table>
                                <button type="button" class="btn btn-secondary" onClick="window.location.href='{entity_varname}.html'">Back</button>
                                <button type="button" class="btn btn-primary float-right" onClick="root.generate()">Generate</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>"""

    source_code += f"""
            <div class="container" v-if="showReport">
                <div class="row">
                    <div class="col-6 text-left d-inline-block">
                        <button id="prev" type="button" class="btn btn-secondary mb-2" onClick="root.showReport = false, root.showError = false"> Back </button>
                        <button type="button" class="btn btn-primary mb-2" onClick="root.download_csv()" :disabled="listview_table.length < 1"> Export as CSV</button>
                        <button id="refresh" type="button" class="btn btn-success mb-2" onClick="root.generate()" :disabled="listview_table.length < 1"> Refresh </button>
                    </div>
                    <div class="col-6">
                    </div>
                </div>

                <div class="row">
                    <div class="col overflow-auto">
                        <table class="table  table-hover table-striped">
                            <thead class="thead-dark">
                                <tr>
                                    <template v-for="column in report_fields" id="report_fields">
                                        <th scope="col">{{{{column.label}}}}</th>
                                    </template>"""
    source_code += f"""         
                                </tr>
                            </thead>
                            <tbody>
                                <template v-for="{entity_varname} in listview_table" id="listview-table">
                                    <tr>
                                        <template v-for="column in report_fields">
                                            <td>{{{{ {entity_varname}[column.field] }}}}</td>
                                        </template>"""
    source_code += f"""             
                                    </tr>
                                </template>
                                <template v-if="listview_table.length < 1">
                                    No records found
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    """
    source_code += cg_loadmod.create()
    source_code += cg_footer.create()

    return textwrap.dedent(source_code)
