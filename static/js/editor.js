let diagramData = { nodes: [], edges: [], groups: [] };
let activeDragNode = null;
let dragOffset = { x: 0, y: 0 };

// Inicializadores de interfaz
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initEventListeners();
});

function initTabs() {
    const tabDoc = document.getElementById('tab-doc');
    const tabReq = document.getElementById('tab-req');
    const panelDoc = document.getElementById('panel-doc');
    const panelReq = document.getElementById('panel-req');

    tabDoc.addEventListener('click', () => {
        tabDoc.classList.add('active');
        tabReq.classList.remove('active');
        panelDoc.classList.add('active');
        panelReq.classList.remove('active');
    });

    tabReq.addEventListener('click', () => {
        tabReq.classList.add('active');
        tabDoc.classList.remove('active');
        panelReq.classList.add('active');
        panelDoc.classList.remove('active');
    });
}

function initEventListeners() {
    document.getElementById('btnProcesarCompleto').addEventListener('click', procesarFlujoCompleto);
    document.getElementById('btnProcesarDirecto').addEventListener('click', procesarFlujoDirecto);
    document.getElementById('btnExportar').addEventListener('click', exportarDiagramaJSON);
}

// Envío a Servidor Flask
async function procesarFlujoCompleto() {
    const texto = document.getElementById('txtCasoNegocio').value;
    mostrarLoader(true);
    try {
        const res = await fetch('/api/generar-desde-documento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ documento: texto })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        renderizarDiagrama(data);
    } catch (err) {
        alert("Error procesando agentes: " + err.message);
    } finally {
        mostrarLoader(false);
    }
}

async function procesarFlujoDirecto() {
    const requisitos = document.getElementById('txtRequisitos').value;
    mostrarLoader(true);
    try {
        const res = await fetch('/api/generar-desde-requisitos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ requisitos: requisitos })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        renderizarDiagrama(data);
    } catch (err) {
        alert("Error en el procesador de diseño: " + err.message);
    } finally {
        mostrarLoader(false);
    }
}

// MOTOR DE DIAGRAMADO (Rendimiento Dinámico)
function renderizarDiagrama(jsonDiagrama) {
    diagramData = jsonDiagrama;
    const container = document.getElementById('nodes-layer');
    container.innerHTML = "";

    // 1. Renderizar Contenedores (Grupos)
    diagramData.groups.forEach(group => {
        const el = document.createElement('div');
        el.className = "diagram-group";
        el.style.left = `${group.x}px`;
        el.style.top = `${group.y}px`;
        el.style.width = `${group.w}px`;
        el.style.height = `${group.h}px`;
        el.innerHTML = `<span class="group-label">${group.label}</span>`;
        container.appendChild(el);
    });

    // 2. Renderizar Nodos lógicos
    diagramData.nodes.forEach(node => {
        const el = document.createElement('div');
        el.className = "diagram-node";
        el.id = `node-${node.id}`;
        el.style.left = `${node.x}px`;
        el.style.top = `${node.y}px`;

        // Si existe un icono de proveedor, lo muestra, si no dibuja un genérico
        const displayIcon = node.icon ? '☁️' : '⚙️'; 
        el.innerHTML = `
            <div class="node-icon">${displayIcon}</div>
            <div class="node-label">${node.label}</div>
        `;
        
        // Registrar eventos de arrastre en tiempo real
        el.addEventListener('mousedown', (e) => startDrag(e, node));
        container.appendChild(el);
    });

    // 3. Trazar Conexiones (Líneas SVG)
    actualizarLineas();
}

// CÁLCULO VECTORIAL PARA LAS CONEXIONES (Sigue el arrastre)
function actualizarLineas() {
    const svg = document.getElementById('canvas-svg');
    svg.innerHTML = `
        <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#888780" />
            </marker>
        </defs>
    `;

    diagramData.edges.forEach(edge => {
        const fromNode = diagramData.nodes.find(n => n.id === edge.from);
        const toNode = diagramData.nodes.find(n => n.id === edge.to);

        if (fromNode && toNode) {
            const line = document.createElementNS("[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)", "line");
            
            // Punto central para origen y destino
            const fromX = fromNode.x + 70; 
            const fromY = fromNode.y + 35;
            const toX = toNode.x + 70;
            const toY = toNode.y + 35;

            line.setAttribute("x1", fromX);
            line.setAttribute("y1", fromY);
            line.setAttribute("x2", toX);
            line.setAttribute("y2", toY);
            line.setAttribute("stroke", edge.color || "#888780");
            line.setAttribute("stroke-width", edge.thickness || 1.5);
            
            if (edge.lineStyle === "dashed") {
                line.setAttribute("stroke-dasharray", "5,5");
            }
            if (edge.endArrow === "arrow") {
                line.setAttribute("marker-end", "url(#arrow)");
            }

            svg.appendChild(line);
        }
    });
}

// FUNCIONES DE ARRASTRE (Drag & Drop)
function startDrag(e, node) {
    if (e.button !== 0) return; // Solo clic izquierdo
    activeDragNode = node;
    const el = document.getElementById(`node-${node.id}`);
    
    dragOffset.x = e.clientX - el.offsetLeft;
    dragOffset.y = e.clientY - el.offsetTop;
    
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
}

function drag(e) {
    if (!activeDragNode) return;
    
    let newX = e.clientX - dragOffset.x;
    let newY = e.clientY - dragOffset.y;

    // Restricciones para mantener el lienzo coherente
    newX = Math.max(0, newX);
    newY = Math.max(0, newY);

    activeDragNode.x = newX;
    activeDragNode.y = newY;

    const el = document.getElementById(`node-${activeDragNode.id}`);
    el.style.left = `${newX}px`;
    el.style.top = `${newY}px`;

    actualizarLineas(); // Vuelve a dibujar el trazado de red durante el movimiento
}

function stopDrag() {
    activeDragNode = null;
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDrag);
}

function mostrarLoader(show) {
    document.getElementById('loader').style.display = show ? 'flex' : 'none';
}

function exportarDiagramaJSON() {
    // Descarga el estado actual modificado por el usuario
    const jsonStr = JSON.stringify(diagramData, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "arquitectura_modificada.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}