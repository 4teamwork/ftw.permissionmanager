jQuery().ready(function($) {
    var principals_tree = $('div.principals_tree');
    principals_tree.parent().hide();

    $('input#principals').select2({
        minimumInputLength: 3,
        width: '400px',
        dropdownCss: {'margin-left': 0},
        ajax: {
            url: './principal_role_tree_search',
            dataType: 'json',
            data: function(term, page) {
                return {search_term: term};
            },
            results: function(data, page){
                return {results: data};
            },
            formatResult: function(item) {
                return item.text;
            }
        }
    }).on('change', function(e){
        if (e.val.length !== 0){
            principals_tree.load(
                './build_principal_role_tree',
                {principalid: $('input#principals').val()},
                function( response, status, xhr ){
                    principals_tree.parent().show();
                });

        } else {
            principals_tree.hide();
        }
    });

});