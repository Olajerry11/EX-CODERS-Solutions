import { createRouter, createWebHistory } from 'vue-router';
import MainLayout from '../layouts/MainLayout.vue';
import { useAuthStore } from '../stores/auth';

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'DashboardPlaceholder',
        component: () => import('../views/DashboardPlaceholder.vue'),
        beforeEnter: (to, from, next) => {
          const auth = useAuthStore();
          if (auth.isLecturer) next({ name: 'LecturerDashboard' });
          else if (auth.isStudent) next({ name: 'StudentDashboard' });
          else next();
        }
      },
      {
        path: 'student',
        name: 'StudentDashboard',
        component: () => import('../views/StudentDashboard.vue'),
        meta: { requiresStudent: true }
      },
      {
        path: 'student/attendance',
        name: 'AttendanceSubmit',
        component: () => import('../views/AttendanceSubmit.vue'),
        meta: { requiresStudent: true }
      },
      {
        path: 'lecturer',
        name: 'LecturerDashboard',
        component: () => import('../views/LecturerDashboard.vue'),
        meta: { requiresLecturer: true }
      },
      {
        path: 'lecturer/attendance/:courseId',
        name: 'GenerateAttendance',
        component: () => import('../views/GenerateAttendance.vue'),
        meta: { requiresLecturer: true }
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Basic Navigation Guards
router.beforeEach((to, from, next) => {
  const auth = useAuthStore();
  
  if (to.meta.requiresLecturer && !auth.isLecturer) {
    return next({ name: 'DashboardPlaceholder' });
  }
  if (to.meta.requiresStudent && !auth.isStudent) {
    return next({ name: 'DashboardPlaceholder' });
  }
  
  next();
});

export default router;
