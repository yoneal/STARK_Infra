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
            <div class="row row-cols-1 row-cols-md-2">
                <template v-for="module in modules" id="modules-template">
                    <div class="col mb-4" id="modules_list">
                        <div class="card h-100 p-2 module_card" :onclick="'window.location.href=\\''  + module.href + '\\''">
                            <img class="card-img-top bg-primary" :src="module.image" :alt="module.image_alt">
                            <div class="card-body bg-dark">
                                <h5 class="card-title text-light">{{{{ module.title }}}}</h5>
                            </div>
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
