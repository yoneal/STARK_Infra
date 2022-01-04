#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

import cgstatic_html_generic_header as cg_header
import cgstatic_html_generic_bodyhead as cg_bodyhead
import cgstatic_html_generic_loadingspinner as cg_loadspin

def create(data):

    source_code  = cg_header.create(data, "HomePage")
    source_code += cg_bodyhead.create(data, "_HomePage")

    source_code += f"""\
        <div class="container-fluid">
            <div class="modules_list_box">
                <div class="row" id="modules_list">
                    <template v-for="module in modules" id="modules-template">
                        <div class="col">
                            <div class="card mb-3 p-2 module_card" :onclick="'window.location.href=\\''  + module.href + '\\''">
                                <img class="card-img-top" :src="module.image" :alt="module.image_alt">
                                <div class="card-body">
                                    <h5 class="card-title">{{{{ module.title }}}}</h5>
                                    <p class="card-text">{{{{ module.description }}}}</p>
                                    <a href="#" class="btn btn-primary w-100">Go</a>
                                </div>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

        </div>

        <div class="d-flex justify-content-center" id="loading-spinner" :style="{{visibility: visibility}}">
            <div class="spinner-border" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        </div>
        </body>
        </html>"""

    return textwrap.dedent(source_code)