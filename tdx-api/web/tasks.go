package main

import (
	"context"
	"sync"
	"time"

	"github.com/google/uuid"
)

type TaskStatus string

const (
	TaskStatusPending   TaskStatus = "pending"
	TaskStatusRunning   TaskStatus = "running"
	TaskStatusSuccess   TaskStatus = "success"
	TaskStatusFailed    TaskStatus = "failed"
	TaskStatusCancelled TaskStatus = "cancelled"
)

type Task struct {
	ID        string     `json:"id"`
	Type      string     `json:"type"`
	Status    TaskStatus `json:"status"`
	Error     string     `json:"error,omitempty"`
	StartedAt time.Time  `json:"started_at"`
	EndedAt   *time.Time `json:"ended_at,omitempty"`
	cancel    context.CancelFunc
}

type TaskManager struct {
	mu    sync.RWMutex
	tasks map[string]*Task
}

func NewTaskManager() *TaskManager {
	return &TaskManager{
		tasks: make(map[string]*Task),
	}
}

func (tm *TaskManager) Run(taskType string, fn func(ctx context.Context) error) string {
	tm.mu.Lock()
	ctx, cancel := context.WithCancel(context.Background())
	id := uuid.New().String()
	task := &Task{
		ID:        id,
		Type:      taskType,
		Status:    TaskStatusRunning,
		StartedAt: time.Now(),
		cancel:    cancel,
	}
	tm.tasks[id] = task
	tm.mu.Unlock()

	go func() {
		err := fn(ctx)

		tm.mu.Lock()
		defer tm.mu.Unlock()

		now := time.Now()
		task.EndedAt = &now

		if err != nil {
			if task.Status != TaskStatusCancelled {
				task.Status = TaskStatusFailed
				task.Error = err.Error()
			}
			return
		}

		if task.Status != TaskStatusCancelled {
			task.Status = TaskStatusSuccess
		}
	}()

	return id
}

func (tm *TaskManager) Cancel(id string) bool {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task, ok := tm.tasks[id]
	if !ok {
		return false
	}

	if task.Status == TaskStatusSuccess || task.Status == TaskStatusFailed || task.Status == TaskStatusCancelled {
		return false
	}

	task.Status = TaskStatusCancelled
	if task.cancel != nil {
		task.cancel()
	}
	now := time.Now()
	task.EndedAt = &now
	return true
}

func (tm *TaskManager) Get(id string) (*Task, bool) {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	task, ok := tm.tasks[id]
	return task, ok
}

func (tm *TaskManager) List() []*Task {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	list := make([]*Task, 0, len(tm.tasks))
	for _, task := range tm.tasks {
		list = append(list, task)
	}
	return list
}
