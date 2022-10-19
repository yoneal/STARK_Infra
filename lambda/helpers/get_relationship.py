#This reads the model of the yaml and get all or the specified entity's relationship

def get_relationship(model, parent_entity_name=""):
    rel_list        = {}
    has_one_list    = []
    has_many_list   = []
    belongs_to_list = []
    for entity, attributes in model.items():
        if type(attributes) is dict:
            cols = attributes['data']
            for col, types in cols.items():
                
                if isinstance(types, dict):
                    for data in types:
                        if data == 'has_one':
                            if parent_entity_name == "":
                                rel={'entity' : entity, 'attribute': types['has_one']}
                                has_one_list.append(rel)
                            else:
                                if col == parent_entity_name:
                                    rel={'entity' : entity, 'attribute': types['has_one']}
                                    has_one_list.append(rel)
                        if data == 'has_many':
                            if parent_entity_name == "":
                                rel={'entity' : col, 'type' : types.get('has_many_ux', 'multi-select-pill')}
                                has_many_list.append(rel)
                            else:
                                if entity == parent_entity_name:
                                    rel={'entity' : col, 'type' : types.get('has_many_ux', 'multi-select-pill')}
                                    has_many_list.append(rel)
                    if entity == parent_entity_name:
                        if types.get('has_one', '') != '':
                            rel={'entity' : col}
                            belongs_to_list.append(rel)

    if len(has_one_list) > 0:
        rel_list.update({'has_one' : has_one_list})
    if len(has_many_list) > 0:
        rel_list.update({'has_many' : has_many_list})
    if len(belongs_to_list) > 0:
        rel_list.update({'belongs_to' : belongs_to_list})
    return rel_list