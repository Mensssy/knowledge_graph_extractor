MATCH (n {name: '机翼'})-[r]-(m)
RETURN n, r, m, type(r) as relationship_type, labels(n) as n_labels, labels(m) as m_labels;

MATCH path = (n {name: 'F-16型机'})-[*1..3]-(m) 
RETURN n, m, path, length(path) as hops 
ORDER BY hops; 

MATCH path = (n {name: '飞行者1号'})-[r:RELATIONSHIP]-(m)
WHERE r.relation_type IN ['具有几何特征']
RETURN n, m, path, r.relation_type as 关系类型, length(path) as hops
ORDER BY hops;
