/** Calendar integration types */

export interface CalendarEvent {
  id?: string;
  title: string;
  description?: string;
  startTime: string;               // ISO datetime
  endTime: string;                 // ISO datetime
  attendees?: string[];            // email addresses
  location?: string;
  meetingUrl?: string;
  calendarId?: string;
}

export interface TimeSlot {
  start: string;                   // ISO datetime
  end: string;                     // ISO datetime
  available: boolean;
}

export interface ScheduleRequest {
  durationMinutes: number;
  attendees: string[];
  preferredTimes?: TimeSlot[];
  title: string;
  description?: string;
}
