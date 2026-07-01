import React, { useEffect, useRef, useState } from 'react'
import {
  MessageSquare,
  Star,
  Archive,
  Trash2,
  MoreHorizontal,
  Check,
  X,
} from 'lucide-react'
import { analystApi } from '../../services/analyst'

function ConversationItem({ conv, isActive, onClick, onRefresh }) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(conv.title)
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    setTitle(conv.title)
  }, [conv.title])

  useEffect(() => {
    if (!showMenu) return undefined

    const handleClickOutside = (event) => {
      if (!menuRef.current?.contains(event.target)) {
        setShowMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showMenu])

  const saveTitle = async () => {
    const nextTitle = title.trim()
    if (!nextTitle) {
      setEditing(false)
      setTitle(conv.title)
      return
    }

    try {
      await analystApi.updateConversation(conv.id, { title: nextTitle })
      setEditing(false)
      onRefresh()
    } catch (e) {
      setEditing(false)
      setTitle(conv.title)
    }
  }

  const toggleFavourite = async (e) => {
    e.stopPropagation()
    await analystApi.updateConversation(conv.id, { is_favourite: !conv.is_favourite })
    onRefresh()
    setShowMenu(false)
  }

  const archive = async (e) => {
    e.stopPropagation()
    await analystApi.updateConversation(conv.id, { status: 'archived' })
    onRefresh()
    setShowMenu(false)
  }

  const remove = async (e) => {
    e.stopPropagation()
    await analystApi.deleteConversation(conv.id)
    onRefresh()
    setShowMenu(false)
  }

  return (
    <div
      onClick={() => !editing && onClick(conv.id)}
      className={`group relative px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
        isActive ? 'bg-prism-900/60 border border-prism-800' : 'hover:bg-gray-800'
      }`}
    >
      <div className="flex items-start gap-2">
        <MessageSquare size={14} className={`mt-0.5 flex-shrink-0 ${isActive ? 'text-prism-400' : 'text-gray-600'}`} />
        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <input
                autoFocus
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') saveTitle()
                  if (e.key === 'Escape') {
                    setEditing(false)
                    setTitle(conv.title)
                  }
                }}
                className="flex-1 bg-gray-700 text-white text-xs rounded px-2 py-0.5 outline-none border border-prism-600"
              />
              <button onClick={saveTitle} className="text-emerald-400"><Check size={12} /></button>
              <button onClick={() => { setEditing(false); setTitle(conv.title) }} className="text-gray-400"><X size={12} /></button>
            </div>
          ) : (
            <p className={`text-sm font-medium truncate ${isActive ? 'text-white' : 'text-gray-300'}`}>
              {conv.title}
            </p>
          )}
          <div className="flex items-center gap-2 mt-0.5">
            {conv.is_favourite && <Star size={10} className="text-amber-400 fill-amber-400" />}
            <span className="text-xs text-gray-600">{conv.message_count} msg{conv.message_count !== 1 ? 's' : ''}</span>
          </div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu) }}
          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-700 text-gray-500 hover:text-gray-300 transition-all"
        >
          <MoreHorizontal size={12} />
        </button>
      </div>

      {showMenu && (
        <div
          ref={menuRef}
          className="absolute right-2 top-8 z-20 bg-gray-800 border border-gray-700 rounded-lg shadow-lg py-1 min-w-[140px]"
          onClick={(e) => e.stopPropagation()}
        >
          <button onClick={(e) => { e.stopPropagation(); setEditing(true); setShowMenu(false) }} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white">Rename</button>
          <button onClick={toggleFavourite} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white">
            <Star size={12} /> {conv.is_favourite ? 'Unfavourite' : 'Favourite'}
          </button>
          <button onClick={archive} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 hover:text-white">
            <Archive size={12} /> Archive
          </button>
          <div className="border-t border-gray-700 my-0.5" />
          <button onClick={remove} className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-gray-700">
            <Trash2 size={12} /> Delete
          </button>
        </div>
      )}
    </div>
  )
}

export default function ConversationList({ conversations, activeId, onSelect, onRefresh, onNew }) {
  const favourites = conversations.filter((conversation) => conversation.is_favourite)
  const recent = conversations.filter((conversation) => !conversation.is_favourite)

  return (
    <div className="flex-1 overflow-y-auto px-2 py-2 space-y-4">
      <button
        onClick={onNew}
        className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-prism-600 hover:bg-prism-500 text-white text-sm font-medium transition-colors"
      >
        + New Conversation
      </button>

      {favourites.length > 0 && (
        <div>
          <p className="text-xs text-gray-600 uppercase tracking-wider px-2 mb-1">Favourites</p>
          {favourites.map((conversation) => (
            <ConversationItem key={conversation.id} conv={conversation} isActive={conversation.id === activeId} onClick={onSelect} onRefresh={onRefresh} />
          ))}
        </div>
      )}

      {recent.length > 0 && (
        <div>
          <p className="text-xs text-gray-600 uppercase tracking-wider px-2 mb-1">Recent</p>
          {recent.map((conversation) => (
            <ConversationItem key={conversation.id} conv={conversation} isActive={conversation.id === activeId} onClick={onSelect} onRefresh={onRefresh} />
          ))}
        </div>
      )}

      {conversations.length === 0 && (
        <p className="text-xs text-gray-600 text-center py-4">No conversations yet. Start a new one above.</p>
      )}
    </div>
  )
}
