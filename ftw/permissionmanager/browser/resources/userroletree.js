jQuery().ready(function($) {
    var principals_tree = $('div.principals_tree');
    var show_link = $('#show_principal_tree');
    show_link.hide();

    show_link.on('click', function(e){
        e.preventDefault();

        principals_tree.load(
            './build_principal_role_tree',
            {principalid: $('input#principals').val()});

    });

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
            show_link.show();
        } else {
            show_link.hide();
        }
    }
  });

});