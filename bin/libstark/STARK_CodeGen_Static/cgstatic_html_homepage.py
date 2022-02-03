#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

import cgstatic_html_generic_header as cg_header
import cgstatic_html_generic_footer as cg_footer
import cgstatic_html_generic_bodyhead as cg_bodyhead
import cgstatic_html_generic_loadingmodal as cg_loadmod
import cgstatic_html_generic_loadingspinner as cg_loadspin

def create(data):

    source_code  = cg_header.create(data, "HomePage")
    source_code += cg_bodyhead.create(data, "_HomePage")

    source_code += f"""\
            <div class="d-flex align-content-start flex-wrap">
                <template v-for="module in modules" id="modules-template">
                    <!--
                    <div class="p-0 m-2 border border-primary module_card w-100 text-nowrap" style="overflow-x: hidden" id="modules_list" :onclick="'window.location.href=\\''  + module.href + '\\''">
                        <img class="bg-primary p-2 m-0" :src="module.image" :alt="module.image_alt" height="50px">
                        <span class="card-text align-middle font-weight-bold pl-2 pr-4">{{{{ module.title }}}}</span>                
                    </div>
                    -->
                    <div class="card p-0 m-2 border module_card" id="modules_list" :onclick="'window.location.href=\\''  + module.href + '\\''">
                        <img class="card-img-top p-3  m-0" :src="module.image" alt="Card image cap" height="100px">
                        <div class="card-body bg-primary p-2 rounded-bottom">
                            <p class="card-text text-light font-weight-bold text-center">{{{{module.title}}}}</p>
                        </div>
                    </div>

                </template>
            </div>

        </div>
"""
    source_code += cg_loadspin.create()
    source_code += cg_loadmod.create()
    source_code += cg_footer.create()

    return textwrap.dedent(source_code)
