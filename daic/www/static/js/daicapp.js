var Containers = {};

Containers.Collection = Backbone.Collection.extend({
    url: '/v1/containers'
});

Containers.Views = {};

Containers.Views.Edit = Backbone.View.extend({
    change: function () {
        this.model.set({
            name: $(this.el).children('input').val()
        });
        this.model.save();
    },
    destroy: function () {
        var el = this.el;
        this.model.destroy({
            success: function () {
                $(el).remove();
            }
        });
    },
    events: {
        'click button': 'destroy',
        'change input': 'change'
    },
    initialize: function () {
        _(this).bindAll('change', 'destroy', 'render');
    },
    render: function () {
        $('#container-template').tmpl(this.model.toJSON()).appendTo(this.el);
        this.delegateEvents();
    }
});

Containers.Views.List = Backbone.View.extend({
    append: function (model) {
        var p = $('<p>').appendTo('#containers'),
            view = new Containers.Views.Edit({
                model: model,
                el: p[0]
            });
        view.render();
    },
    initialize: function () {
        _(this).bindAll('append', 'render');
        this.collection.bind('refresh', this.render);
        this.collection.bind('add', this.append);
    },
    render: function () {
        $('#containers').empty();
        this.collection.each(function (model) {
            this.append(model);
        }, this);
    }
});
$(function () {
    var collection = new Containers.Collection(),
        view = new Containers.Views.List({
            collection: collection
        });

    collection.fetch();

    $('#add').click(function () {
        var model = new Backbone.Model({
            name: $('#new-name').val()
        });
        collection.add(model);
        model.save();
    });
});
