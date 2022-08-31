var sidebar = new Vue({
    el: "#mySidenav",
    data: {
        group_collapse_name: 'nav-group-collapse-1',
        modules: ''
    },
    methods:{
        get_module_list: function () {
            //FIXME: When default permissions and module registry are implemented in PreLaunch, this should become the default endpoint for homepage modules
            fetchUrl = STARK.STARK_Module_url + '?rt=usermodules'
            //fetchUrl = STARK.sys_modules_url
            STARK.request('GET', fetchUrl)
            .then( function(data) {
                const grouped_modules = []

                grouping = []
                grouping_ctr = 0

                for (const key in data['items']) {
                    data['items'].sort((a, b) => b.priority - a.priority)

                    group = data['items'][key]['group']
                    if ( group in grouping ) {
                        //Skip
                    }
                    else {
                        module_grp = data['module_grps'].find(element=>element.Group_Name == group)
                        grouping[group] = grouping_ctr
                        grouped_modules[grouping_ctr] = {
                            "group_name": group,
                            "priority": module_grp['Priority'],
                            "modules": []
                        }
                        grouping_ctr++
                    }
                    grouped_modules[grouping[group]]["modules"].push(data['items'][key])
                }
                grouped_modules.sort((a, b) => b.priority - a.priority)
                // console.log(grouped_modules)
                console.log("Hi")

                sidebar.modules = grouped_modules;
                console.log(sidebar.modules)
                console.log("DONE! Retrieved list of modules.")
                spinner.hide();
            })                    
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]");
            });
        }
    }
})

sidebar.get_module_list();

function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
    document.getElementById("main").style.marginLeft = "250px";
}
    
function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("main").style.marginLeft= "0";
}
