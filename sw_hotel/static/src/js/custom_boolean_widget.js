odoo.define('sw_hotel.CustomBooleanWidget', function(require) {
    'use strict';

    var basic_fields = require('web.basic_fields');
    var field_registry = require('web.field_registry');

    var CustomBooleanWidget = basic_fields.FieldBoolean.extend({
        init: function() {
            this._super.apply(this, arguments);
        },
        _render: function() {
            this.$el.empty();
            var value = this.value ? 'Yes' : 'No';
            this.$el.addClass(this.value ? 'boolean-true' : 'boolean-false')
            this.$el.text(value);
        },
    });

    field_registry.add('custom_boolean_widget', CustomBooleanWidget);

    return {
        CustomBooleanWidget: CustomBooleanWidget,
    };
});
