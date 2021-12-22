/**
 * Converts the data from server to connections array
 * @param {Array} data - data received from server through websocket
 * @return {Array} An array having arrays of connections
 */
function dataToConnections(data){
    const connections = {}
    for (const [a, b] of data) {
        connections[Object.keys(a)[0]] = [
            Object.keys(b)[0]
        ]
    }
    return connections
}

/**
 * Converts the data from server to Objects array of the nodes
 * @param {Array} data - data received from server through websocket
 * @return {Array} An array having arrays of Objects representation of data from server. 
 * Every object represents a node and has properties such as inputs, outputs, config.. for that node
 */
function dataToObjects(data){
    const connections = {}
    for (const [a, b] of data) {
        connections[Object.keys(a)[0]] = a[Object.keys(a)[0]]
        connections[Object.keys(b)[0]] = b[Object.keys(b)[0]]
    }
    return connections
}

/**
 * Converts the data from server to connections array
 * @param {Array} connections - connections between nodes generated from server data
 * @return {Array} Elements array having Nodes for graph representation. A sample graph Node has id, data and position
 */
 function connectionsToNodes(connections){
    connections['RollingAverager'].push('Node4', 'Node5', 'Node2')
    connections['Node2'] = ['Node6', 'Node7']
    const adjacencyListKeys = Object.keys(connections)
    console.log("adjacency list keys", adjacencyListKeys)
    console.log("connections are" , connections)
    // adding all nodes of the graph without duplicates
    const allNodes = Object.keys(connections)
    for (let [, edgeNodes] of Object.entries(connections)) {
        for (let n of edgeNodes) {
            if (!allNodes.includes(n)) {
            allNodes.push(n)
            }
        }
    }
    // generating the elements list having nodes with their properties
    const elements = []
    for (let node of allNodes) {
        elements.push({
            id: node,
            data: { label: node },
            position: 0,
        })
    }

    const elements_index = {}

    for (let i = 0; i < elements.length; i++) {
        const node = elements[i].id
        elements_index[node] = i
    }

    // generating the edges between every source and target node
    for (let i = 0; i < adjacencyListKeys.length; i++) {
        const node = adjacencyListKeys[i]
        const edgeNodes = connections[node]
        let j = -1
        for (let edgeNode of edgeNodes) {
            elements.push({ id: `e-${node}-${edgeNode}`, source: node, target: edgeNode, animated: true },)
            j ++
        }
    }

    console.log(elements)

    return elements
 }

module.exports = {
    dataToConnections,
    dataToObjects,
    connectionsToNodes,
}

