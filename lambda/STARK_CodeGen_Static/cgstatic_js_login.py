#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap

def create(data):

    source_code = f"""\
        var root = new Vue({{
            el: "#vue-root",
            data: {{
                form: {{
                    username: '',
                    password: '',
                }},
                error_message: '&nbsp;'
            }},
            methods: {{

                login: function (payload) {{

                    fetchUrl = STARK.login_url
                    return STARK.request('POST', fetchUrl, payload)
                }},
            
                submit: function () {{
                    root.error_message = "&nbsp;"
                    loading_modal.show()
                    console.log("Logging in!")

                    let data = {{ Login: this.form }}

                    this.login(data).then( function(data) {{
                        console.log("Response received from login endpoint!");
                        loading_modal.hide()
                        console.log(data)

                        //Determine response is success or failure.
                        //If success, create cookie with the supplied session_id
                        //Else, show error message
                        if(data['message'] == 'AuthSuccess') {{
                            console.log('Legit!')
                            window.location.href = "home.html";
                        }}
                        else {{
                            console.log("Invalid username or password!")
                            root.error_message = "Invalid username or password!"
                        }}
        
                    }}).catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    }});
                }}
            }}
        }})
    """
    return textwrap.dedent(source_code)