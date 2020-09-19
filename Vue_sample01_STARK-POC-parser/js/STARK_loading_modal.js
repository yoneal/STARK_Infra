var loading_modal = new Vue({
    el: "#loading-modal",
    data: {
        visibility: 'visible'
    },
    methods: {
        show: function () {
            loading_modal.$bvModal.show('loading-modal');
        },
        hide: function () {
            loading_modal.$bvModal.hide('loading-modal');
        }
    }
})
