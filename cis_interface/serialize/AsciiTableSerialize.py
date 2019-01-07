from cis_interface import backwards, serialize, units
from cis_interface.serialize import register_serializer
from cis_interface.serialize.DefaultSerialize import DefaultSerialize
from cis_interface.metaschema.properties.ScalarMetaschemaProperties import (
    definition2dtype)


@register_serializer
class AsciiTableSerialize(DefaultSerialize):
    r"""Class for serialize table output into bytes messages comprising a
    formatted ASCII table.

    Args:
        format_str (str, optional): If provided, this string will be used to
            format messages from a list of arguments and parse messages to
            get a list of arguments in C printf/scanf style. Defaults to
            None and messages are assumed to already be bytes.
        field_names (list, optional): The names of fields in the format string.
            If not provided, names are set based on the order of the fields in
            the format string.
        field_units (list, optional): The units of fields in the format string.
            If not provided, all fields are assumed to be dimensionless.
        as_array (bool, optional): If True, each of the arguments being
            serialized/deserialized will be arrays that are converted to/from
            bytes in column major ('F') order. Otherwise, each argument should
            be a scalar. Defaults to False.
        delimiter (str, optional): Character(s) that should be used to separate
            columns. Defaults to '\t'.
        use_astropy (bool, optional): If True, the astropy package will be used
            to serialize/deserialize table. Defaults to False.
        **kwargs: Additional keyword args are processed as part of the type
            definition.

    Attributes:
        format_str (str): Format string used to format/parse bytes messages
            from/to a list of arguments in C printf/scanf style.
        field_names (list): The names of fields in the format string.
        field_units (list): The units of fields in the format string.
        as_array (bool): True or False depending if serialized/deserialized
            python objects will be arrays or scalars.
        delimiter (str): Character(s) that should be used to separate columns.
        use_astropy (bool): If True, the astropy package will be used to
            serialize/deserialize table.

    """

    _seritype = 'ascii_table'
    _schema_properties = dict(
        DefaultSerialize._schema_properties,
        format_str={'type': 'string'},
        field_names={'type': 'array', 'items': {'type': 'string'}},
        field_units={'type': 'array', 'items': {'type': 'string'}},
        as_array={'type': 'boolean', 'default': False},
        delimiter={'type': 'unicode',
                   'default': backwards.bytes2unicode(serialize._default_delimiter)},
        newline={'type': 'unicode',
                 'default': backwards.bytes2unicode(serialize._default_newline)},
        comment={'type': 'unicode',
                 'default': backwards.bytes2unicode(serialize._default_comment)},
        use_astropy={'type': 'boolean', 'default': False})

    def update_serializer(self, *args, **kwargs):
        out = super(AsciiTableSerialize, self).update_serializer(*args, **kwargs)
        if self.typedef['type'] == 'array':
            self.update_format_str()
            self.update_field_names()
            self.update_field_units()
        return out

    def update_format_str(self):
        r"""Update the format string based on the type definition."""
        # Get format information from precision etc.
        assert(self.typedef['type'] == 'array')
        if self.format_str is None:
            fmts = []
            if isinstance(self.typedef['items'], dict):  # pragma: debug
                idtype = definition2dtype(self.typedef['items'])
                ifmt = serialize.nptype2cformat(idtype, asbytes=True)
                # fmts = [ifmt for x in msg]
                raise Exception("Variable number of items not yet supported.")
            elif isinstance(self.typedef['items'], list):
                for x in self.typedef['items']:
                    idtype = definition2dtype(x)
                    ifmt = serialize.nptype2cformat(idtype, asbytes=True)
                    fmts.append(ifmt)
            if fmts:
                self._format_str = serialize.table2format(
                    fmts=fmts,
                    delimiter=backwards.unicode2bytes(self.delimiter),
                    newline=backwards.unicode2bytes(self.newline),
                    comment=backwards.unicode2bytes(''))

    def update_field_names(self):
        r"""list: Names for each field in the data type."""
        assert(self.typedef['type'] == 'array')
        if self.field_names is None:
            if isinstance(self.typedef['items'], dict):  # pragma: debug
                raise Exception("Variable number of items not yet supported.")
            elif isinstance(self.typedef['items'], list):
                out = []
                any_names = False
                for i, x in enumerate(self.typedef['items']):
                    out.append(backwards.unicode2bytes(x.get('title', 'f%d' % i)))
                    if 'title' in x:
                        any_names = True
                # Don't use field names if they are all defaults
                if any_names:
                    self.field_names = out

    def update_field_units(self):
        r"""list: Units for each field in the data type."""
        assert(self.typedef['type'] == 'array')
        if self.field_units is None:
            if isinstance(self.typedef['items'], dict):  # pragma: debug
                raise Exception("Variable number of items not yet supported.")
            elif isinstance(self.typedef['items'], list):
                out = []
                any_units = False
                for i, x in enumerate(self.typedef['items']):
                    out.append(backwards.unicode2bytes(x.get('units', '')))
                    if len(x.get('units', '')) > 0:
                        any_units = True
                # Don't use field units if they are all defaults
                if any_units:
                    self.field_units = out

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes, str: Serialized message.

        """
        if self.format_str is None:
            raise RuntimeError("Format string is not defined.")
        if self.as_array:
            args = self.datatype.coerce_type(args)
            out = serialize.array_to_table(args, self.format_str,
                                           use_astropy=self.use_astropy)
        else:
            out = serialize.format_message(args, self.format_str)
        return backwards.unicode2bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg: Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        if self.format_str is None:
            raise RuntimeError("Format string is not defined.")
        if self.as_array:
            out = serialize.table_to_array(msg, self.format_str,
                                           use_astropy=self.use_astropy,
                                           names=self.field_names)
            out = self.datatype.coerce_type(out)
        else:
            out = list(serialize.process_message(msg, self.format_str))
        if self.field_units is not None:
            out = [units.add_units(x, backwards.bytes2unicode(u))
                   for x, u in zip(out, self.field_units)]
        return out
