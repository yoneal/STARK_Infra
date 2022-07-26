#This reads the model of the yaml and get all or the specified entity's relationship

def get_relationship(data, parent_entity_name=""):
    rel_list = []
    for entity, attributes in data.items():
        if type(attributes) is dict:
            cols = attributes['data']
            for col, types in cols.items():
                if type(types) is dict:
                    for data in types:
                        if data == 'has_one':
                            if parent_entity_name == "":
                                rel={'parent' : col, 'child' : entity, 'attribute': types['has_one']}
                                rel_list.append(rel)
                            else:
                                if col == parent_entity_name:
                                    rel={'parent' : col, 'child' : entity, 'attribute': types['has_one']}
                                    rel_list.append(rel)
                                    

    return rel_list