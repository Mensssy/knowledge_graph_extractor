// 删除现有数据
MATCH (n) DETACH DELETE n;

CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name);

:auto CALL {
  LOAD CSV WITH HEADERS FROM 'file:///triplets.csv' AS row
  
  // Merge Head Node (Subject) with its Type
  MERGE (h:Entity {name: trim(row.head), type: trim(row.head_type)})
  
  // Merge Tail Node (Object) with its Type
  MERGE (t:Entity {name: trim(row.tail), type: trim(row.tail_type)})
  
  // Create Relationship (Predicate)
  // We create a relationship from Head to Tail with the actual relation type as a property
  // We filter out empty strings to ensure data integrity
  WITH h, t, row
  WHERE trim(row.relation) <> '' AND trim(row.head) <> '' AND trim(row.tail) <> ''
  MERGE (h)-[r:RELATIONSHIP]->(t)
  SET r.relation_type = trim(row.relation)
  SET r.evidence = trim(row.evidence)
  SET r.id = row.id
} IN TRANSACTIONS OF 1000 ROWS;

// Verify Import Results
MATCH (n:Entity) RETURN count(n) AS total_nodes;
MATCH ()-[r]->() RETURN count(r) AS total_relationships;

MATCH (a:Entity)-[r]->(b:Entity)
RETURN a, r, b
LIMIT 100;
