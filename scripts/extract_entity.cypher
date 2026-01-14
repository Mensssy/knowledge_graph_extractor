// Query 1: Find the "尾翼" node and all its relationships
// This returns the node and its connected relationships without connected nodes
MATCH (n {name: '尾翼'})-[r]->()
RETURN n, r, type(r) as relationship_type, labels(n) as node_labels;

// ============================================
// Query 2: Find "尾翼" node and all directly connected nodes
// This returns the complete subgraph: the entity, relationships, and connected nodes
MATCH (n {name: '尾翼'})-[r]-(m)
RETURN n, r, m, type(r) as relationship_type, labels(n) as n_labels, labels(m) as m_labels;

// ============================================
// Query 3: Find "尾翼" node with outgoing relationships only
MATCH (n {name: '尾翼'})-[r:RELATED_TO|HAS_PROPERTY|BELONGS_TO|PART_OF]->(m)
RETURN n, r, m, type(r) as relationship_type;

// ============================================
// Query 4: Find "尾翼" node with incoming relationships only
MATCH (n {name: '尾翼'})<-[r:RELATED_TO|HAS_PROPERTY|BELONGS_TO|PART_OF]-(m)
RETURN n, r, m, type(r) as relationship_type;

// ============================================
// Query 5: Find "尾翼" node and return as a clean result table
MATCH (n {name: '尾翼'})-[r]-(m)
RETURN 
  n.name as source_entity,
  type(r) as relationship,
  m.name as target_entity,
  labels(n)[0] as source_type,
  labels(m)[0] as target_type;

// ============================================
// Query 6: Find "尾翼" node with 2-hop relationships
// This includes direct connections and connections of connections
MATCH path = (n {name: '尾翼'})-[*1..2]-(m)
RETURN path, n, relationships(path) as relations, m;

// ============================================
// Query 7: Count relationships of "尾翼" node
MATCH (n {name: '尾矢'})-[r]-()
RETURN 
  type(r) as relationship_type,
  count(r) as relationship_count
ORDER BY relationship_count DESC;

// ============================================
// Query 8: Find "尾翼" node if it doesn't exist in name property
// Alternative: Try searching in different properties
MATCH (n)
WHERE n.name = '尾翼' OR n.entity_name = '尾翼' OR n.label = '尾翼'
RETURN n, labels(n);

// ============================================
// Query 9: Extract all data about "尾翼" in JSON format
MATCH (n {name: '尾翼'})-[r]-(m)
RETURN {
  entity: {
    name: n.name,
    labels: labels(n)
  },
  relationships: collect({
    type: type(r),
    direction: CASE 
      WHEN startNode(r) = n THEN 'outgoing'
      ELSE 'incoming'
    END,
    related_entity: {
      name: m.name,
      labels: labels(m)
    }
  })
} as result;

// ============================================
// Usage Instructions:
// 1. Open Neo4j Browser or connect to Neo4j via your preferred client
// 2. Uncomment the query you want to execute (remove the "//" at the start of each line)
// 3. Execute the query by pressing Ctrl+Enter or clicking the Run button
// 4. For Neo4j Browser, you can also select a specific query block and run it
//
// Recommended: Start with Query 2 to see all connected nodes and relationships
// ============================================
