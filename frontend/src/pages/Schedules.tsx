import { python } from '@codemirror/lang-python'
import { EditorView } from '@codemirror/view'
import CodeMirror from '@uiw/react-codemirror'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { useApi } from '@/hooks/use-api'
import {
  getSchedules as apiGetSchedules,
  updateSchedule as apiUpdateSchedule,
} from '@/lib/api'
import { Schedule } from '@/models'

import { Layout } from './Layout'

export default function Schedules() {
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(
    null
  )
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)
  const { scheduleId: selectedScheduleId } = useParams()
  const navigate = useNavigate()
  const {
    data: schedules,
    setData: setSchedules,
    loading: schedulesLoading,
    fn: getSchedules,
  } = useApi<Schedule[], typeof apiGetSchedules>(apiGetSchedules, true)
  const { loading: updateLoading, fn: updateSchedule } =
    useApi(apiUpdateSchedule)

  useEffect(() => {
    if (selectedScheduleId && schedules) {
      const schedule = schedules.find((s) => s.id === selectedScheduleId)
      setSelectedSchedule(schedule || null)
      setEditingSchedule(null)
    } else {
      setSelectedSchedule(null)
    }
  }, [selectedScheduleId, schedules])

  useEffect(() => {
    getSchedules()
  }, [])

  const saveSchedule = (schedule: Schedule): void => {
    updateSchedule(schedule).then((new_schedule) => {
      setSchedules(
        schedules?.map((s) => (s.id === new_schedule.id ? new_schedule : s)) ||
          []
      )
    })
  }

  const formatNextRun = (dateString: Date | null): string => {
    if (!dateString) return 'Not scheduled'
    return new Date(dateString).toLocaleString()
  }

  return (
    <Layout>
      <div className="flex gap-6 h-[calc(100vh-200px)]">
        <Card className="w-80 flex-shrink-0">
          <CardHeader>
            <CardTitle>All Schedules</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-full overflow-y-auto">
              {schedulesLoading ? (
                <div className="space-y-2 p-4">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : schedules && schedules.length > 0 ? (
                <div className="space-y-1">
                  {schedules.map((schedule: Schedule) => (
                    <button
                      key={schedule.id}
                      onClick={() => {
                        navigate('/ragpile/schedules/' + schedule.id)
                      }}
                      className={`w-full text-left p-4 border-b hover:bg-gray-50 transition-colors ${
                        selectedScheduleId === schedule.id
                          ? 'bg-blue-50 border-l-4 border-l-blue-500'
                          : ''
                      }`}
                    >
                      <div className="font-medium text-sm text-gray-600">
                        {schedule.name ||
                          `Schedule ${schedule.id.slice(0, 8)}...`}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Crontab: {schedule.crontab}
                      </div>
                      <div className="text-xs text-gray-500">
                        Next: {formatNextRun(schedule.next_run_time)}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-gray-500">
                  No schedules found
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Schedule Details Panel */}
        <Card className="flex-1">
          <CardHeader>
            <CardTitle>
              {selectedSchedule
                ? `${selectedSchedule.name || `Schedule ${selectedSchedule.id.slice(0, 8)}...`}`
                : 'Select a schedule to view details'}
            </CardTitle>
            {selectedSchedule && !editingSchedule && (
              <div className="flex gap-2">
                <Button
                  onClick={() => setEditingSchedule({ ...selectedSchedule })}
                  className="w-fit"
                >
                  Edit
                </Button>
                <Button
                  className="w-fit"
                  onClick={() =>
                    saveSchedule({ ...selectedSchedule, state: 'paused' })
                  }
                >
                  Pause
                </Button>
                <Button
                  className="w-fit"
                  onClick={() =>
                    saveSchedule({
                      ...selectedSchedule,
                      state: 'running',
                    })
                  }
                >
                  Resume
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent>
            {selectedSchedule ? (
              <div className="space-y-4">
                {editingSchedule ? (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Name</Label>
                      <Input
                        id="name"
                        type="text"
                        value={editingSchedule.name}
                        onChange={(e) =>
                          setEditingSchedule({
                            ...editingSchedule,
                            name: e.target.value,
                          })
                        }
                        placeholder="Schedule name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="crontab">Crontab</Label>
                      <Input
                        id="crontab"
                        type="string"
                        value={editingSchedule.crontab}
                        onChange={(e) =>
                          setEditingSchedule({
                            ...editingSchedule,
                            crontab: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="code">Python Code</Label>
                      <CodeMirror
                        value={editingSchedule.code}
                        onChange={(value) =>
                          setEditingSchedule({
                            ...editingSchedule,
                            code: value,
                          })
                        }
                        extensions={[python(), EditorView.lineWrapping]}
                        theme="dark"
                        basicSetup={{
                          lineNumbers: true,
                          foldGutter: false,
                          dropCursor: false,
                          allowMultipleSelections: false,
                        }}
                        className="border border-input rounded-md"
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          saveSchedule(editingSchedule)
                        }}
                        disabled={updateLoading}
                      >
                        {updateLoading ? 'Saving...' : 'Save'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setEditingSchedule(null)}
                        disabled={updateLoading}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <Label>Name</Label>
                      <div className="text-sm text-gray-700 mt-1">
                        {selectedSchedule.name || 'Unnamed'}
                      </div>
                    </div>
                    <div>
                      <Label>Crontab</Label>
                      <div className="text-sm text-gray-700 mt-1">
                        {selectedSchedule.crontab}
                      </div>
                    </div>
                    <div>
                      <Label>Next Run Time</Label>
                      <div className="text-sm text-gray-700 mt-1">
                        {formatNextRun(selectedSchedule.next_run_time)}
                      </div>
                    </div>
                    <div>
                      <Label>Python Code</Label>
                      <CodeMirror
                        value={selectedSchedule.code}
                        extensions={[python(), EditorView.lineWrapping]}
                        theme="dark"
                        editable={false}
                        basicSetup={{
                          lineNumbers: true,
                          foldGutter: false,
                          dropCursor: false,
                          allowMultipleSelections: false,
                        }}
                        className="border border-gray-200 rounded-md mt-2"
                      />
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-500">
                Select a schedule from the left to view its details
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
