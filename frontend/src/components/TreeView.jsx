import React, { useState } from 'react'

function TreeNode({ node, labelKey, onSelect, onEdit, onDelete, selectedId, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2)
  const hasChildren = node.children && node.children.length > 0
  const isSelected = selectedId === node.id

  return (
    <div>
      <div
        className={`flex items-center gap-1 py-1 px-2 rounded cursor-pointer group
          ${isSelected ? 'bg-primary-100 text-primary-800' : 'hover:bg-slate-100'}`}
        style={{ paddingLeft: `${(depth * 16) + 8}px` }}
        onClick={() => onSelect && onSelect(node)}
      >
        {hasChildren ? (
          <button
            className="w-4 h-4 flex items-center justify-center text-slate-400 hover:text-slate-600 shrink-0"
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          >
            {expanded ? '▾' : '▸'}
          </button>
        ) : (
          <span className="w-4 shrink-0" />
        )}
        <span className="flex-1 text-sm truncate">{node[labelKey]}</span>
        {(onEdit || onDelete) && (
          <span className="hidden group-hover:flex gap-1">
            {onEdit && (
              <button
                className="text-xs text-slate-500 hover:text-primary-600 px-1"
                onClick={(e) => { e.stopPropagation(); onEdit(node) }}
                title="Editar"
              >✎</button>
            )}
            {onDelete && (
              <button
                className="text-xs text-slate-500 hover:text-red-600 px-1"
                onClick={(e) => { e.stopPropagation(); onDelete(node) }}
                title="Eliminar"
              >✕</button>
            )}
          </span>
        )}
      </div>
      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              labelKey={labelKey}
              onSelect={onSelect}
              onEdit={onEdit}
              onDelete={onDelete}
              selectedId={selectedId}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function TreeView({ nodes = [], labelKey = 'name', onSelect, onEdit, onDelete, selectedId }) {
  if (!nodes.length) {
    return <p className="text-sm text-slate-400 italic px-3 py-4">Sin elementos.</p>
  }
  return (
    <div className="select-none">
      {nodes.map((node) => (
        <TreeNode
          key={node.id}
          node={node}
          labelKey={labelKey}
          onSelect={onSelect}
          onEdit={onEdit}
          onDelete={onDelete}
          selectedId={selectedId}
        />
      ))}
    </div>
  )
}
