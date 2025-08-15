import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
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

  const handleEditClick = () => {
    if (selectedSchedule) {
      setEditingSchedule({ ...selectedSchedule })
    }
  }

  const handleSaveClick = async () => {
    if (editingSchedule) {
      await updateSchedule(editingSchedule)
      setEditingSchedule(null)
      getSchedules()
    }
  }

  const handleCancelClick = () => {
    setEditingSchedule(null)
  }

  const formatInterval = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
    return `${Math.floor(seconds / 86400)}d`
  }

  const formatNextRun = (dateString: Date | null) => {
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
                      <div className="font-medium text-sm text-gray-900">
                        Schedule {schedule.id.slice(0, 8)}...
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Interval: {formatInterval(schedule.interval_seconds)}
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
              {selectedScheduleId
                ? `Schedule - ${selectedScheduleId.slice(0, 8)}...`
                : 'Select a schedule to view details'}
            </CardTitle>
            {selectedSchedule && !editingSchedule && (
              <Button onClick={handleEditClick} className="w-fit">
                Edit
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {selectedSchedule ? (
              <div className="space-y-4">
                {editingSchedule ? (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="interval">Interval (seconds)</Label>
                      <Input
                        id="interval"
                        type="number"
                        value={editingSchedule.interval_seconds}
                        onChange={(e) =>
                          setEditingSchedule({
                            ...editingSchedule,
                            interval_seconds: parseInt(e.target.value) || 0,
                          })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="code">Python Code</Label>
                      <Textarea
                        id="code"
                        value={editingSchedule.code}
                        onChange={(e) =>
                          setEditingSchedule({
                            ...editingSchedule,
                            code: e.target.value,
                          })
                        }
                        className="font-mono text-sm min-h-[400px]"
                        placeholder="Enter Python code here..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleSaveClick}
                        disabled={updateLoading}
                      >
                        {updateLoading ? 'Saving...' : 'Save'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={handleCancelClick}
                        disabled={updateLoading}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <Label>Interval</Label>
                      <div className="text-sm text-gray-700 mt-1">
                        {formatInterval(selectedSchedule.interval_seconds)} (
                        {selectedSchedule.interval_seconds} seconds)
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
                      <pre className="bg-gray-100 p-4 rounded-md text-sm font-mono overflow-x-auto mt-2 whitespace-pre-wrap text-gray-900">
                        {selectedSchedule.code}
                      </pre>
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
