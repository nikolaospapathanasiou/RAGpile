import { useEffect, useState } from 'react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useApi } from '@/hooks/use-api'
import {
  getThread as apiGetThread,
  getThreads as apiGetThreads,
} from '@/lib/api'
import { Thread, ThreadItem } from '@/models'

import { Layout } from './Layout'

export default function Threads() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null)

  const {
    data: threads,
    loading: threadsLoading,
    fn: getThreads,
  } = useApi<ThreadItem[], typeof apiGetThreads>(apiGetThreads, true)
  const { loading: threadLoading, fn: fetchThread } = useApi(apiGetThread)

  useEffect(() => {
    if (selectedThreadId) {
      fetchThread(selectedThreadId).then(setSelectedThread)
    } else {
      setSelectedThread(null)
    }
  }, [selectedThreadId])

  useEffect(() => {
    getThreads()
  }, [])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <Layout>
      <div className="flex gap-6 h-[calc(100vh-200px)]">
        <Card className="w-80 flex-shrink-0">
          <CardHeader>
            <CardTitle>All Threads</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-full overflow-y-auto">
              {threadsLoading ? (
                <div className="space-y-2 p-4">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : threads && threads.length > 0 ? (
                <div className="space-y-1">
                  {threads.map((thread: ThreadItem) => (
                    <button
                      key={thread.id}
                      onClick={() => setSelectedThreadId(thread.id)}
                      className={`w-full text-left p-4 border-b hover:bg-gray-50 transition-colors ${
                        selectedThreadId === thread.id
                          ? 'bg-blue-50 border-l-4 border-l-blue-500'
                          : ''
                      }`}
                    >
                      <div className="font-medium text-sm text-gray-900">
                        Thread {thread.id.slice(0, 8)}...
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(thread.created_at)}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-gray-500">
                  No threads found
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Messages Panel */}
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>
              {selectedThreadId
                ? `Messages - Thread ${selectedThreadId.slice(0, 8)}...`
                : 'Select a thread to view messages'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {threadLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ) : selectedThread ? (
              <div className="space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto">
                {selectedThread.channel_values.messages.map(
                  (message, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg ${
                        message.type === 'human'
                          ? 'bg-blue-50 ml-4'
                          : 'bg-gray-50 mr-4'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-xs font-medium px-2 py-1 rounded ${
                            message.type === 'human'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {message.type === 'human'
                            ? 'You'
                            : 'Assistant' + ' (' + message.type + ')'}
                        </span>
                      </div>
                      <div className="text-sm text-gray-900 whitespace-pre-wrap">
                        {message.content ?? null}
                        {message.tool_calls &&
                          message.tool_calls.map((tool_call) => (
                            <div
                              key={tool_call.id}
                              className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-md"
                            >
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-xs font-medium px-2 py-1 bg-amber-100 text-amber-800 rounded">
                                  🔧 Tool Call
                                </span>
                                <span className="text-sm font-medium text-amber-900">
                                  {tool_call.name}
                                </span>
                              </div>
                              {tool_call.args &&
                                Object.keys(tool_call.args).length > 0 && (
                                  <div className="space-y-1">
                                    <div className="text-xs font-medium text-amber-700 mb-1">
                                      Arguments:
                                    </div>
                                    {Object.entries(tool_call.args).map(
                                      ([key, value]) => (
                                        <div key={key} className="text-xs">
                                          <span className="font-medium text-amber-800">
                                            {key}:
                                          </span>{' '}
                                          <span className="text-amber-700 font-mono bg-amber-100 px-1 rounded">
                                            {typeof value === 'string'
                                              ? value
                                              : JSON.stringify(value)}
                                          </span>
                                        </div>
                                      )
                                    )}
                                  </div>
                                )}
                            </div>
                          ))}
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-500">
                Select a thread from the left to view its messages
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
