jQuery().ready(function($) {

  $('input#principals').select2({
    minimumInputLength: 3,
    width: '400px',
    multiple: true,
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
  });

});