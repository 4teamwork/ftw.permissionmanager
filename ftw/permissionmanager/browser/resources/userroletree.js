jQuery().ready(function($) {
    var principals_tree = $('ul.principals_tree');
    var remove_link = $('a[href*="@@remove_user_permissions"]');
    var copy_link = $('a[href*="@@copy_user_permissions"]');

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

                    remove_link.attr('href', remove_link.attr('href').replace(/\?user=.*/g, '?user=' + e.val));
                    copy_link.attr('href', copy_link.attr('href').replace(/\?source_user=.*/g, '?source_user=' + e.val));
                });

        } else {
            principals_tree.hide();
        }
    });

});