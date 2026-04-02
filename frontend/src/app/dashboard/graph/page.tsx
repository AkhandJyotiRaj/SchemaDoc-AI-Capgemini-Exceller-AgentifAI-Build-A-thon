"use client";

import { useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PipelineRun } from "@/lib/api";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Node,
  Edge,
  Position,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { GitFork, Table2 } from "lucide-react";

// ── Custom Table Node ───────────────────────────────────────────
function TableNode({ data }: { data: any }) {
  return (
    <div className="min-w-[180px] rounded-xl border border-zinc-700 bg-zinc-900 shadow-xl shadow-black/30">
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-blue-500 !w-2 !h-2 !border-zinc-700"
      />
      <div className="flex items-center gap-2 rounded-t-xl border-b border-zinc-700 bg-zinc-800 px-3 py-2">
        <Table2 className="h-3.5 w-3.5 text-blue-400" />
        <span className="text-xs font-semibold text-zinc-100">
          {data.label}
        </span>
        {data.fkCount > 0 && (
          <span className="ml-auto text-[9px] text-blue-400/60">
            {data.fkCount} FK
          </span>
        )}
      </div>
      <div className="max-h-48 overflow-y-auto px-3 py-2 text-[11px]">
        {data.columns?.slice(0, 10).map((col: any) => (
          <div
            key={col.name}
            className="flex items-center justify-between py-0.5"
          >
            <span
              className={
                col.is_primary_key
                  ? "font-medium text-amber-400"
                  : col.is_foreign_key
                    ? "text-blue-400"
                    : "text-zinc-400"
              }
            >
              {col.is_primary_key ? "🔑 " : col.is_foreign_key ? "🔗 " : ""}
              {col.name}
            </span>
            <span className="ml-3 text-zinc-600">{col.type || ""}</span>
          </div>
        ))}
        {data.columns?.length > 10 && (
          <div className="mt-1 text-center text-zinc-600">
            +{data.columns.length - 10} more
          </div>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-blue-500 !w-2 !h-2 !border-zinc-700"
      />
    </div>
  );
}

const nodeTypes = { tableNode: TableNode };

// ── Build Graph Data ────────────────────────────────────────────
function buildGraph(schema: Record<string, any>) {
  const tables = Object.entries(schema);
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const cols = Math.ceil(Math.sqrt(tables.length));

  // Helper to normalize columns dict to array
  const normalizeCols = (columns: any) => {
    if (Array.isArray(columns)) return columns;
    if (!columns || typeof columns !== "object") return [];
    return Object.entries(columns).map(([k, v]: [string, any]) => ({
      name: v.name || k,
      type: v.original_type || v.type || "",
      is_primary_key: v.is_primary_key ?? false,
      is_foreign_key: v.is_foreign_key ?? false,
      ...v,
    }));
  };

  tables.forEach(([name, table], i) => {
    const row = Math.floor(i / cols);
    const col = i % cols;
    const colsArray = normalizeCols(table.columns);

    nodes.push({
      id: name,
      type: "tableNode",
      position: { x: col * 300, y: row * 350 },
      data: {
        label: name,
        columns: colsArray,
        fkCount: (table.foreign_keys || []).length,
      },
    });

    // Create edges from table-level foreign_keys array
    (table.foreign_keys || []).forEach((fk: any) => {
      const refTable = fk.referred_table;
      if (refTable && schema[refTable]) {
        edges.push({
          id: `${name}-${fk.column}-${refTable}`,
          source: name,
          target: refTable,
          type: "smoothstep",
          animated: true,
          style: { stroke: "#3b82f6", strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: "#3b82f6" },
          label: fk.column,
          labelStyle: { fontSize: 10, fill: "#71717a" },
        });
      }
    });

    // Also check column-level FK references
    colsArray.forEach((column: any) => {
      if (column.is_foreign_key && column.references) {
        const refTable =
          typeof column.references === "string"
            ? column.references.split(".")[0]
            : column.references.table;
        if (refTable && schema[refTable]) {
          const edgeId = `${name}-${column.name}-${refTable}`;
          if (!edges.find((e) => e.id === edgeId)) {
            edges.push({
              id: edgeId,
              source: name,
              target: refTable,
              type: "smoothstep",
              animated: true,
              style: { stroke: "#3b82f6", strokeWidth: 1.5 },
              markerEnd: { type: MarkerType.ArrowClosed, color: "#3b82f6" },
              label: column.name,
              labelStyle: { fontSize: 10, fill: "#71717a" },
            });
          }
        }
      }
    });
  });

  return { nodes, edges };
}

// ── Graph Page ──────────────────────────────────────────────────
export default function GraphPage() {
  const { data: runs = [] } = useQuery<PipelineRun[]>({
    queryKey: ["runs"],
    queryFn: api.listRuns,
  });

  const latestRun = runs.length > 0 ? runs[0] : null;
  const schema = latestRun?.result || {};

  const { nodes, edges } = useMemo(() => buildGraph(schema), [schema]);

  if (!latestRun || Object.keys(schema).length === 0) {
    return (
      <div className="flex h-[70vh] flex-col items-center justify-center text-zinc-600">
        <GitFork className="mb-4 h-12 w-12" />
        <p className="text-sm">
          Run the pipeline to visualize the entity-relationship graph.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Knowledge Graph</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Entity-relationship diagram &mdash; {nodes.length} tables,{" "}
          {edges.length} relationships
        </p>
      </div>

      <div className="h-[calc(100vh-200px)] overflow-hidden rounded-xl border border-zinc-800">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
          style={{ background: "#09090b" }}
        >
          <Background color="#27272a" gap={24} size={1} />
          <Controls />
          <MiniMap
            nodeColor="#3b82f6"
            maskColor="rgba(0,0,0,0.7)"
            style={{ backgroundColor: "#18181b", borderColor: "#27272a" }}
          />
        </ReactFlow>
      </div>
    </div>
  );
}
