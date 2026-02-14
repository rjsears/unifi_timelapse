<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--color-text-primary);">Timelapses</h1>
        <p style="color: var(--color-text-muted);">View and manage timelapse videos</p>
      </div>
      <button
        v-if="activeTab === 'videos'"
        class="btn-primary"
        @click="showGenerateModal = true"
      >
        <PlayIcon class="w-5 h-5 mr-2" />
        Generate Timelapse
      </button>
      <button
        v-else-if="activeTab === 'configs'"
        class="btn-primary"
        @click="openAddConfigModal"
      >
        <PlusIcon class="w-5 h-5 mr-2" />
        Add Timelapse
      </button>
    </div>

    <!-- Tabs -->
    <div class="border-b" style="border-color: var(--color-border);">
      <nav class="flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="[
            'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
            activeTab === tab.id
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent hover:border-gray-300 dark:hover:border-slate-600',
          ]"
          :style="activeTab !== tab.id ? { color: 'var(--color-text-secondary)' } : {}"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- Videos Tab -->
    <template v-if="activeTab === 'videos'">
      <!-- Filters -->
      <div class="card p-4">
        <div class="flex flex-wrap gap-4">
          <select v-model="filters.camera" class="input w-auto">
            <option value="">All Cameras</option>
            <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
              {{ camera.name }}
            </option>
          </select>
          <select v-model="filters.status" class="input w-auto">
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
          <select v-model="filters.type" class="input w-auto">
            <option value="">All Types</option>
            <option value="daily">Daily</option>
            <option value="multiday">Multi-day</option>
          </select>
        </div>
      </div>

      <!-- Timelapse list -->
      <div class="card">
        <div v-if="loading" class="flex justify-center py-12">
          <div class="spinner w-8 h-8"></div>
        </div>
        <div v-else-if="timelapses.length === 0" class="text-center py-12">
          <FilmIcon class="w-12 h-12 mx-auto" style="color: var(--color-text-muted);" />
          <h3 class="mt-4 text-lg font-medium" style="color: var(--color-text-primary);">No timelapses found</h3>
          <p class="mt-2" style="color: var(--color-text-muted);">Timelapses will appear here once generated.</p>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
          <div
            v-for="timelapse in timelapses"
            :key="timelapse.id"
            class="rounded-lg border overflow-hidden shadow-sm"
            style="background-color: var(--color-surface); border-color: var(--color-border);"
          >
            <!-- Thumbnail -->
            <div class="aspect-video relative" style="background-color: var(--color-bg-secondary);">
              <img
                v-if="timelapse.status === 'completed'"
                :src="`/api/timelapses/${timelapse.id}/thumbnail`"
                class="w-full h-full object-cover"
                @error="$event.target.style.display = 'none'"
              />
              <div class="absolute inset-0 flex items-center justify-center">
                <div
                  v-if="timelapse.status === 'processing'"
                  class="bg-gray-900/80 px-3 py-2 rounded-lg flex items-center text-white"
                >
                  <div class="spinner w-4 h-4 mr-2"></div>
                  Processing...
                </div>
                <PlayCircleIcon
                  v-else-if="timelapse.status === 'completed'"
                  class="w-12 h-12 text-white/80 cursor-pointer hover:text-white"
                  @click="playTimelapse(timelapse)"
                />
              </div>
            </div>
            <!-- Info -->
            <div class="p-4">
              <div class="flex items-center justify-between mb-2">
                <h3 class="font-medium" style="color: var(--color-text-primary);">{{ timelapse.camera_name }}</h3>
                <span :class="statusClass(timelapse.status)">{{ timelapse.status }}</span>
              </div>
              <p class="text-sm" style="color: var(--color-text-muted);">
                {{ formatDateRange(timelapse) }}
              </p>
              <div v-if="timelapse.status === 'completed'" class="mt-2 text-xs" style="color: var(--color-text-muted);">
                {{ timelapse.frame_count }} frames • {{ formatDuration(timelapse.duration_seconds) }}
              </div>
              <div v-if="timelapse.status === 'failed'" class="mt-2 text-xs text-red-500">
                {{ timelapse.error_message }}
              </div>
              <!-- Actions -->
              <div class="mt-4 flex items-center space-x-2">
                <button
                  v-if="timelapse.status === 'completed'"
                  class="btn-secondary text-xs px-3 py-1"
                  @click="downloadTimelapse(timelapse)"
                >
                  <ArrowDownTrayIcon class="w-4 h-4 mr-1" />
                  Download
                </button>
                <button
                  class="btn-secondary text-xs px-3 py-1 text-red-500 hover:text-red-600"
                  @click="confirmDelete(timelapse)"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Scheduled Timelapses Tab -->
    <template v-if="activeTab === 'configs'">
      <div class="card">
        <div v-if="configsLoading" class="flex justify-center py-12">
          <div class="spinner w-8 h-8"></div>
        </div>
        <div v-else-if="multidayConfigs.length === 0" class="text-center py-12">
          <CalendarDaysIcon class="w-12 h-12 mx-auto" style="color: var(--color-text-muted);" />
          <h3 class="mt-4 text-lg font-medium" style="color: var(--color-text-primary);">No scheduled timelapses</h3>
          <p class="mt-2" style="color: var(--color-text-muted);">Create a schedule for multi-day timelapses.</p>
          <button class="btn-primary mt-4" @click="openAddConfigModal">
            <PlusIcon class="w-5 h-5 mr-2" />
            Add Timelapse
          </button>
        </div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Camera</th>
              <th>Mode</th>
              <th>Schedule / Progress</th>
              <th>Coverage</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="config in multidayConfigs" :key="config.id">
              <td class="font-medium" style="color: var(--color-text-primary);">{{ config.name }}</td>
              <td style="color: var(--color-text-secondary);">{{ getCameraName(config.camera_id) }}</td>
              <td style="color: var(--color-text-secondary);">
                <span :class="config.mode === 'prospective' ? 'badge-info' : 'badge'">
                  {{ config.mode === 'prospective' ? 'Prospective' : 'Historical' }}
                </span>
              </td>
              <td style="color: var(--color-text-secondary);">
                <template v-if="config.mode === 'prospective' && config.status === 'collecting'">
                  <div class="flex items-center space-x-2">
                    <div class="w-24 rounded-full h-2" style="background-color: var(--color-bg-secondary);">
                      <div
                        class="bg-primary-500 h-2 rounded-full"
                        :style="{ width: config.collection_progress_percent + '%' }"
                      ></div>
                    </div>
                    <span class="text-xs">
                      Day {{ config.collection_progress_days }}/{{ config.days_to_include }}
                    </span>
                  </div>
                </template>
                <template v-else>
                  {{ formatDay(config.generation_day) }} {{ formatTime(config.generation_time) }}
                </template>
              </td>
              <td style="color: var(--color-text-secondary);">
                {{ config.days_to_include }} days, {{ config.images_per_hour }}/hr
              </td>
              <td>
                <span :class="getConfigStatusClass(config)">
                  {{ getConfigStatusLabel(config) }}
                </span>
              </td>
              <td>
                <div class="flex items-center space-x-2">
                  <button
                    class="hover:text-primary-600" style="color: var(--color-text-muted);"
                    title="Edit"
                    @click="openEditConfigModal(config)"
                  >
                    <PencilIcon class="w-4 h-4" />
                  </button>
                  <template v-if="config.mode === 'prospective'">
                    <button
                      v-if="config.status === 'idle'"
                      class="hover:text-green-600" style="color: var(--color-text-muted);"
                      title="Start Collection"
                      @click="startProspectiveCollection(config)"
                    >
                      <PlayIcon class="w-4 h-4" />
                    </button>
                    <button
                      v-else-if="config.status === 'collecting'"
                      class="hover:text-red-500" style="color: var(--color-text-muted);"
                      title="Cancel Collection"
                      @click="cancelProspectiveCollection(config)"
                    >
                      <StopIcon class="w-4 h-4" />
                    </button>
                    <button
                      v-else-if="config.status === 'ready'"
                      class="hover:text-green-600" style="color: var(--color-text-muted);"
                      title="Generate Timelapse"
                      @click="triggerConfig(config)"
                    >
                      <FilmIcon class="w-4 h-4" />
                    </button>
                  </template>
                  <template v-else>
                    <button
                      class="hover:text-green-600" style="color: var(--color-text-muted);"
                      title="Trigger Now"
                      @click="triggerConfig(config)"
                    >
                      <PlayIcon class="w-4 h-4" />
                    </button>
                  </template>
                  <button
                    class="hover:text-red-500" style="color: var(--color-text-muted);"
                    title="Delete"
                    @click="confirmDeleteConfig(config)"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Custom Timelapse Tab (Historical Mode) -->
    <template v-if="activeTab === 'custom'">
      <div class="card p-6">
        <h3 class="text-lg font-medium mb-4" style="color: var(--color-text-primary);">Generate Custom Timelapse</h3>
        <p class="mb-6" style="color: var(--color-text-muted);">
          Create a one-off timelapse from existing images. Select a date range and video settings.
        </p>

        <form @submit.prevent="generateCustomTimelapse" class="space-y-6">
          <!-- Camera Selection -->
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Camera</label>
            <select
              v-model="customForm.camera_id"
              class="input"
              required
              @change="loadAvailableDates"
            >
              <option value="">Select a camera</option>
              <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
                {{ camera.name }}
              </option>
            </select>
          </div>

          <!-- Available Dates Info -->
          <div v-if="customForm.camera_id && availableDatesData">
            <div class="rounded-lg p-4 mb-4" style="background-color: var(--color-bg-secondary);">
              <div class="flex items-center justify-between text-sm">
                <span style="color: var(--color-text-secondary);">Available Images:</span>
                <span class="font-medium" style="color: var(--color-text-primary);">{{ availableDatesData.total_images.toLocaleString() }}</span>
              </div>
              <div class="flex items-center justify-between text-sm mt-1">
                <span style="color: var(--color-text-secondary);">Date Range:</span>
                <span class="font-medium" v-if="availableDatesData.oldest_date" style="color: var(--color-text-primary);">
                  {{ formatDate(availableDatesData.oldest_date) }} - {{ formatDate(availableDatesData.newest_date) }}
                </span>
                <span v-else style="color: var(--color-text-muted);">No images available</span>
              </div>
            </div>
          </div>

          <!-- Date Range -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Start Date</label>
              <input
                v-model="customForm.start_date"
                type="date"
                class="input"
                :min="availableDatesData?.oldest_date"
                :max="customForm.end_date || availableDatesData?.newest_date"
                required
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">End Date</label>
              <input
                v-model="customForm.end_date"
                type="date"
                class="input"
                :min="customForm.start_date || availableDatesData?.oldest_date"
                :max="availableDatesData?.newest_date"
                required
              />
            </div>
          </div>

          <!-- Video Settings -->
          <div class="border-t pt-4" style="border-color: var(--color-border);">
            <h4 class="text-sm font-medium mb-4" style="color: var(--color-text-primary);">Video Settings</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Images/Hour</label>
                <input
                  v-model.number="customForm.images_per_hour"
                  type="number"
                  min="1"
                  max="60"
                  class="input"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Frame Rate</label>
                <input
                  v-model.number="customForm.frame_rate"
                  type="number"
                  min="1"
                  max="120"
                  class="input"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">CRF (Quality)</label>
                <input
                  v-model.number="customForm.crf"
                  type="number"
                  min="0"
                  max="51"
                  class="input"
                  required
                />
                <p class="text-xs mt-1" style="color: var(--color-text-muted);">Lower = better</p>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Pixel Format</label>
                <select v-model="customForm.pixel_format" class="input" required>
                  <option value="yuv420p">yuv420p</option>
                  <option value="yuv444p">yuv444p</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Estimated Output -->
          <div v-if="customForm.start_date && customForm.end_date" class="rounded-lg p-4 bg-blue-100 dark:bg-blue-500/20">
            <div class="text-sm text-blue-800 dark:text-blue-300">
              <strong>Estimated:</strong>
              {{ estimatedFrames }} frames
              (~{{ estimatedDuration }} at {{ customForm.frame_rate }}fps)
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-end">
            <button
              type="submit"
              class="btn-primary"
              :disabled="!customForm.camera_id || !customForm.start_date || !customForm.end_date || generatingCustom"
            >
              <template v-if="generatingCustom">
                <div class="spinner w-4 h-4 mr-2"></div>
                Generating...
              </template>
              <template v-else>
                <PlayIcon class="w-5 h-5 mr-2" />
                Generate Timelapse
              </template>
            </button>
          </div>
        </form>
      </div>
    </template>

    <!-- Generate Modal -->
    <Modal v-model="showGenerateModal" title="Generate Timelapse" size="md">
      <form @submit.prevent="generateTimelapse" class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Camera</label>
          <select v-model="generateForm.camera_id" class="input" required>
            <option value="">Select a camera</option>
            <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
              {{ camera.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Date</label>
          <input v-model="generateForm.date" type="date" class="input" required />
        </div>
        <div class="flex justify-end space-x-3 pt-4">
          <button type="button" class="btn-secondary" @click="showGenerateModal = false">
            Cancel
          </button>
          <button type="submit" class="btn-primary">Generate</button>
        </div>
      </form>
    </Modal>

    <!-- Video Player Modal -->
    <Modal v-model="showPlayerModal" :title="playingTimelapse?.camera_name" size="full">
      <div class="aspect-video bg-black rounded-lg overflow-hidden">
        <video
          v-if="playingTimelapse"
          :src="`/api/timelapses/${playingTimelapse.id}/video`"
          controls
          autoplay
          class="w-full h-full"
        ></video>
      </div>
    </Modal>

    <!-- Delete confirmation -->
    <Modal v-model="showDeleteModal" title="Delete Timelapse" size="sm">
      <p style="color: var(--color-text-secondary);">
        Are you sure you want to delete this timelapse?
      </p>
      <div class="flex justify-end space-x-3 pt-6">
        <button class="btn-secondary" @click="showDeleteModal = false">Cancel</button>
        <button class="btn-danger" @click="deleteTimelapse">Delete</button>
      </div>
    </Modal>

    <!-- Timelapse Add/Edit Modal -->
    <Modal v-model="showConfigModal" :title="editingConfig ? 'Edit Scheduled Timelapse' : 'Add Scheduled Timelapse'" size="lg">
      <form @submit.prevent="saveConfig" class="space-y-4">
        <!-- Mode Selection -->
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2" style="color: var(--color-text-secondary);">Mode</label>
          <div class="flex space-x-4">
            <label class="flex items-center">
              <input
                type="radio"
                v-model="configForm.mode"
                value="historical"
                class="mr-2"
                :disabled="editingConfig && editingConfig.status === 'collecting'"
              />
              <span style="color: var(--color-text-secondary);">Historical (Look Back)</span>
            </label>
            <label class="flex items-center">
              <input
                type="radio"
                v-model="configForm.mode"
                value="prospective"
                class="mr-2"
                :disabled="editingConfig && editingConfig.status === 'collecting'"
              />
              <span style="color: var(--color-text-secondary);">Prospective (Collect Forward)</span>
            </label>
          </div>
          <p class="text-xs mt-1" style="color: var(--color-text-muted);">
            <template v-if="configForm.mode === 'historical'">
              Generates timelapse from past images on a schedule.
            </template>
            <template v-else>
              Protects images as they're captured, then generates when collection completes.
            </template>
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Name</label>
            <input
              v-model="configForm.name"
              type="text"
              class="input"
              placeholder="Weekly Summary"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Camera</label>
            <select
              v-model="configForm.camera_id"
              class="input"
              :disabled="!!editingConfig"
              required
            >
              <option value="">Select a camera</option>
              <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
                {{ camera.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Historical mode: Schedule -->
        <template v-if="configForm.mode === 'historical'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Generation Day</label>
              <select v-model="configForm.generation_day" class="input" required>
                <option value="sunday">Sunday</option>
                <option value="monday">Monday</option>
                <option value="tuesday">Tuesday</option>
                <option value="wednesday">Wednesday</option>
                <option value="thursday">Thursday</option>
                <option value="friday">Friday</option>
                <option value="saturday">Saturday</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Generation Time</label>
              <input
                v-model="configForm.generation_time"
                type="time"
                class="input"
                required
              />
            </div>
          </div>
        </template>

        <!-- Prospective mode: Auto-generate -->
        <template v-else>
          <div class="rounded-lg p-4 bg-blue-100 dark:bg-blue-500/20">
            <label class="flex items-center">
              <input v-model="configForm.auto_generate" type="checkbox" class="mr-2" />
              <span style="color: var(--color-text-secondary);">Auto-generate when collection completes</span>
            </label>
            <p class="text-xs mt-1" style="color: var(--color-text-muted);">
              Start collection from the Scheduled Timelapses tab after creating.
            </p>
          </div>
        </template>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Days to Include</label>
            <input
              v-model.number="configForm.days_to_include"
              type="number"
              min="1"
              max="365"
              class="input"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Images per Hour</label>
            <input
              v-model.number="configForm.images_per_hour"
              type="number"
              min="1"
              max="60"
              class="input"
              required
            />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Frame Rate</label>
            <input
              v-model.number="configForm.frame_rate"
              type="number"
              min="1"
              max="120"
              class="input"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">CRF (Quality)</label>
            <input
              v-model.number="configForm.crf"
              type="number"
              min="0"
              max="51"
              class="input"
              required
            />
            <p class="mt-1 text-xs" style="color: var(--color-text-muted);">Lower = better quality</p>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Pixel Format</label>
            <select v-model="configForm.pixel_format" class="input" required>
              <option value="yuv420p">yuv420p (Recommended)</option>
              <option value="yuv444p">yuv444p (High Quality)</option>
              <option value="rgb24">rgb24</option>
            </select>
          </div>
        </div>

        <div class="flex items-center">
          <label class="flex items-center">
            <input v-model="configForm.is_enabled" type="checkbox" class="mr-2" />
            <span style="color: var(--color-text-secondary);">Enabled</span>
          </label>
        </div>

        <div class="flex justify-end space-x-3 pt-4">
          <button type="button" class="btn-secondary" @click="showConfigModal = false">
            Cancel
          </button>
          <button type="submit" class="btn-primary">
            {{ editingConfig ? 'Save Changes' : 'Create Schedule' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- Config Delete Confirmation -->
    <Modal v-model="showDeleteConfigModal" title="Delete Scheduled Timelapse" size="sm">
      <p style="color: var(--color-text-secondary);">
        Are you sure you want to delete the configuration "{{ configToDelete?.name }}"?
      </p>
      <div class="flex justify-end space-x-3 pt-6">
        <button class="btn-secondary" @click="showDeleteConfigModal = false">Cancel</button>
        <button class="btn-danger" @click="deleteConfig">Delete</button>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { format } from 'date-fns'
import api from '@/api'
import { useNotificationsStore } from '@/stores/notifications'
import { useMultidayStore } from '@/stores/multiday'
import Modal from '@/components/ui/Modal.vue'
import {
  PlayIcon,
  PlusIcon,
  FilmIcon,
  PlayCircleIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  CalendarDaysIcon,
  PencilIcon,
  StopIcon,
} from '@heroicons/vue/24/outline'

const notifications = useNotificationsStore()
const multidayStore = useMultidayStore()

const activeTab = ref('videos')
const tabs = [
  { id: 'videos', name: 'Videos' },
  { id: 'configs', name: 'Scheduled Timelapses' },
  { id: 'custom', name: 'Custom Timelapse' },
]

const loading = ref(false)
const timelapses = ref([])
const cameras = ref([])
const showGenerateModal = ref(false)
const showPlayerModal = ref(false)
const showDeleteModal = ref(false)
const playingTimelapse = ref(null)
const timelapseToDelete = ref(null)

// Config state
const showConfigModal = ref(false)
const showDeleteConfigModal = ref(false)
const editingConfig = ref(null)
const configToDelete = ref(null)

const configsLoading = computed(() => multidayStore.loading)
const multidayConfigs = computed(() => multidayStore.configs)

const filters = ref({
  camera: '',
  status: '',
  type: '',
})

const generateForm = ref({
  camera_id: '',
  date: format(new Date(), 'yyyy-MM-dd'),
})

const defaultConfigForm = {
  camera_id: '',
  name: '',
  is_enabled: true,
  images_per_hour: 2,
  days_to_include: 7,
  generation_day: 'sunday',
  generation_time: '02:00',
  frame_rate: 30,
  crf: 20,
  pixel_format: 'yuv444p',
  mode: 'historical',
  auto_generate: true,
}

const configForm = ref({ ...defaultConfigForm })

// Custom timelapse state
const customForm = ref({
  camera_id: '',
  start_date: '',
  end_date: '',
  images_per_hour: 2,
  frame_rate: 30,
  crf: 20,
  pixel_format: 'yuv444p',
})
const availableDatesData = ref(null)
const loadingDates = computed(() => multidayStore.loadingDates)
const generatingCustom = ref(false)

// Computed for custom timelapse estimates
const estimatedFrames = computed(() => {
  if (!customForm.value.start_date || !customForm.value.end_date) return 0
  const start = new Date(customForm.value.start_date)
  const end = new Date(customForm.value.end_date)
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
  return days * 24 * customForm.value.images_per_hour
})

const estimatedDuration = computed(() => {
  const frames = estimatedFrames.value
  if (!frames || !customForm.value.frame_rate) return '0:00'
  const seconds = frames / customForm.value.frame_rate
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
})

async function loadTimelapses() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.camera) params.append('camera_id', filters.value.camera)
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.type) params.append('type', filters.value.type)

    const response = await api.get(`/timelapses?${params}`)
    timelapses.value = response.data.timelapses || []
  } catch (error) {
    notifications.error('Error', 'Failed to load timelapses')
  } finally {
    loading.value = false
  }
}

async function loadCameras() {
  try {
    const response = await api.get('/cameras')
    cameras.value = response.data.cameras || []
  } catch (error) {
    console.error('Failed to load cameras:', error)
  }
}

async function generateTimelapse() {
  try {
    await api.post(`/timelapses/camera/${generateForm.value.camera_id}`, {
      date_start: generateForm.value.date,
      date_end: generateForm.value.date,
    })
    notifications.success('Started', 'Timelapse generation started')
    showGenerateModal.value = false
    await loadTimelapses()
  } catch (error) {
    notifications.error('Error', error.response?.data?.detail || 'Failed to start generation')
  }
}

function playTimelapse(timelapse) {
  playingTimelapse.value = timelapse
  showPlayerModal.value = true
}

function downloadTimelapse(timelapse) {
  window.open(`/api/timelapses/${timelapse.id}/download`, '_blank')
}

function confirmDelete(timelapse) {
  timelapseToDelete.value = timelapse
  showDeleteModal.value = true
}

async function deleteTimelapse() {
  try {
    await api.delete(`/timelapses/${timelapseToDelete.value.id}`)
    notifications.success('Deleted', 'Timelapse deleted')
    showDeleteModal.value = false
    await loadTimelapses()
  } catch (error) {
    notifications.error('Error', 'Failed to delete timelapse')
  }
}

function statusClass(status) {
  const classes = {
    completed: 'badge-success',
    processing: 'badge-info',
    pending: 'badge-warning',
    failed: 'badge-danger',
  }
  return classes[status] || 'badge'
}

function formatDateRange(timelapse) {
  if (!timelapse.date_start) return 'N/A'
  try {
    if (timelapse.date_start === timelapse.date_end) {
      return format(new Date(timelapse.date_start), 'MMM d, yyyy')
    }
    return `${format(new Date(timelapse.date_start), 'MMM d')} - ${format(new Date(timelapse.date_end), 'MMM d, yyyy')}`
  } catch {
    return 'Invalid date'
  }
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Config functions
function getCameraName(cameraId) {
  const camera = cameras.value.find(c => c.id === cameraId)
  return camera?.name || 'Unknown'
}

function formatDay(day) {
  return day.charAt(0).toUpperCase() + day.slice(1)
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  // Handle both "HH:MM" and "HH:MM:SS" formats
  const parts = timeStr.split(':')
  const hours = parseInt(parts[0], 10)
  const minutes = parts[1]
  const ampm = hours >= 12 ? 'PM' : 'AM'
  const hour12 = hours % 12 || 12
  return `${hour12}:${minutes} ${ampm}`
}

function openAddConfigModal() {
  editingConfig.value = null
  configForm.value = { ...defaultConfigForm }
  showConfigModal.value = true
}

function openEditConfigModal(config) {
  editingConfig.value = config
  configForm.value = {
    camera_id: config.camera_id,
    name: config.name,
    is_enabled: config.is_enabled,
    images_per_hour: config.images_per_hour,
    days_to_include: config.days_to_include,
    generation_day: config.generation_day,
    generation_time: config.generation_time.slice(0, 5), // Convert "HH:MM:SS" to "HH:MM"
    frame_rate: config.frame_rate,
    crf: config.crf,
    pixel_format: config.pixel_format,
    mode: config.mode || 'historical',
    auto_generate: config.auto_generate !== false,
  }
  showConfigModal.value = true
}

async function saveConfig() {
  if (editingConfig.value) {
    // Update existing config
    const result = await multidayStore.updateConfig(editingConfig.value.id, {
      name: configForm.value.name,
      is_enabled: configForm.value.is_enabled,
      images_per_hour: configForm.value.images_per_hour,
      days_to_include: configForm.value.days_to_include,
      generation_day: configForm.value.generation_day,
      generation_time: configForm.value.generation_time,
      frame_rate: configForm.value.frame_rate,
      crf: configForm.value.crf,
      pixel_format: configForm.value.pixel_format,
      mode: configForm.value.mode,
      auto_generate: configForm.value.auto_generate,
    })
    if (result.success) {
      notifications.success('Saved', 'Scheduled timelapse updated')
      showConfigModal.value = false
    } else {
      notifications.error('Error', result.error)
    }
  } else {
    // Create new config
    const result = await multidayStore.createConfig({
      camera_id: configForm.value.camera_id,
      name: configForm.value.name,
      is_enabled: configForm.value.is_enabled,
      images_per_hour: configForm.value.images_per_hour,
      days_to_include: configForm.value.days_to_include,
      generation_day: configForm.value.generation_day,
      generation_time: configForm.value.generation_time,
      frame_rate: configForm.value.frame_rate,
      crf: configForm.value.crf,
      pixel_format: configForm.value.pixel_format,
      mode: configForm.value.mode,
      auto_generate: configForm.value.auto_generate,
    })
    if (result.success) {
      notifications.success('Created', 'Scheduled timelapse created')
      showConfigModal.value = false
    } else {
      notifications.error('Error', result.error)
    }
  }
}

function confirmDeleteConfig(config) {
  configToDelete.value = config
  showDeleteConfigModal.value = true
}

async function deleteConfig() {
  const result = await multidayStore.deleteConfig(configToDelete.value.id)
  if (result.success) {
    notifications.success('Deleted', 'Scheduled timelapse deleted')
    showDeleteConfigModal.value = false
  } else {
    notifications.error('Error', result.error)
  }
}

async function triggerConfig(config) {
  const result = await multidayStore.triggerGeneration(config.id)
  if (result.success) {
    notifications.success('Triggered', 'Multi-day timelapse generation started')
  } else {
    notifications.error('Error', result.error)
  }
}

// Custom timelapse functions
async function loadAvailableDates() {
  if (!customForm.value.camera_id) {
    availableDatesData.value = null
    return
  }
  const result = await multidayStore.getAvailableDates(customForm.value.camera_id)
  if (result.success) {
    availableDatesData.value = result.data
    // Set default dates if available
    if (result.data.oldest_date && result.data.newest_date) {
      customForm.value.end_date = result.data.newest_date
      // Default to 7 days back from newest, or oldest if less than 7 days
      const newest = new Date(result.data.newest_date)
      const oldest = new Date(result.data.oldest_date)
      const sevenDaysAgo = new Date(newest)
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6)
      customForm.value.start_date = sevenDaysAgo < oldest
        ? result.data.oldest_date
        : sevenDaysAgo.toISOString().split('T')[0]
    }
  }
}

async function generateCustomTimelapse() {
  generatingCustom.value = true
  try {
    const result = await multidayStore.generateHistorical({
      camera_id: customForm.value.camera_id,
      start_date: customForm.value.start_date,
      end_date: customForm.value.end_date,
      images_per_hour: customForm.value.images_per_hour,
      frame_rate: customForm.value.frame_rate,
      crf: customForm.value.crf,
      pixel_format: customForm.value.pixel_format,
    })
    if (result.success) {
      notifications.success('Started', result.result.message)
      // Switch to videos tab to see the progress
      activeTab.value = 'videos'
      await loadTimelapses()
    } else {
      notifications.error('Error', result.error)
    }
  } finally {
    generatingCustom.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    return format(new Date(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

// Prospective collection functions
async function startProspectiveCollection(config) {
  const result = await multidayStore.startCollection(config.id, config.days_to_include)
  if (result.success) {
    notifications.success('Started', `Collecting images for ${config.days_to_include} days`)
    await multidayStore.fetchConfigs()
  } else {
    notifications.error('Error', result.error)
  }
}

async function cancelProspectiveCollection(config) {
  if (!confirm('Cancel collection? You can optionally unprotect collected images.')) {
    return
  }
  const unprotect = confirm('Also unprotect collected images? (Cancel = keep protected)')
  const result = await multidayStore.cancelCollection(config.id, unprotect)
  if (result.success) {
    notifications.success('Cancelled', result.result.message)
    await multidayStore.fetchConfigs()
  } else {
    notifications.error('Error', result.error)
  }
}

function getConfigStatusClass(config) {
  if (config.mode === 'prospective') {
    const statusClasses = {
      idle: 'badge',
      collecting: 'badge-info',
      ready: 'badge-success',
      completed: 'badge-success',
      failed: 'badge-danger',
    }
    return statusClasses[config.status] || 'badge'
  }
  return config.is_enabled ? 'badge-success' : 'badge'
}

function getConfigStatusLabel(config) {
  if (config.mode === 'prospective') {
    const labels = {
      idle: 'Idle',
      collecting: 'Collecting',
      ready: 'Ready',
      completed: 'Completed',
      failed: 'Failed',
    }
    return labels[config.status] || config.status
  }
  return config.is_enabled ? 'Enabled' : 'Disabled'
}

watch(filters, loadTimelapses, { deep: true })

watch(activeTab, (newTab) => {
  if (newTab === 'configs') {
    multidayStore.fetchConfigs()
  }
})

onMounted(() => {
  loadCameras()
  loadTimelapses()
})
</script>
