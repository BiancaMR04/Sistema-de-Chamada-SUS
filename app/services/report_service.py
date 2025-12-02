"""
Report generation service.
"""
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy import func

from app import db
from app.models import (
    QueueEntry, CallHistory, AbsenceRecord, Room, Patient,
    CallStatus
)


class ReportService:
    """Service for generating reports."""
    
    @staticmethod
    def get_daily_summary(report_date: Optional[date] = None, room_id: Optional[int] = None) -> dict:
        """
        Generate a daily summary report.
        
        Args:
            report_date: Date for the report (default: today)
            room_id: Filter by room (optional)
            
        Returns:
            Summary statistics dict
        """
        if not report_date:
            report_date = date.today()
        
        base_query = QueueEntry.query.filter(
            func.date(QueueEntry.created_at) == report_date
        )
        
        if room_id:
            base_query = base_query.filter(QueueEntry.room_id == room_id)
        
        total_patients = base_query.count()
        
        attended = base_query.filter(
            QueueEntry.status == CallStatus.ATTENDED.value
        ).count()
        
        absent = base_query.filter(
            QueueEntry.status == CallStatus.ABSENT.value
        ).count()
        
        waiting = base_query.filter(
            QueueEntry.status == CallStatus.WAITING.value
        ).count()
        
        called = base_query.filter(
            QueueEntry.status == CallStatus.CALLED.value
        ).count()
        
        cancelled = base_query.filter(
            QueueEntry.status == CallStatus.CANCELLED.value
        ).count()
        
        # Calculate average wait time for attended patients
        attended_entries = base_query.filter(
            QueueEntry.status == CallStatus.ATTENDED.value,
            QueueEntry.called_at.isnot(None)
        ).all()
        
        avg_wait_time = None
        if attended_entries:
            wait_times = []
            for entry in attended_entries:
                if entry.called_at and entry.created_at:
                    wait_time = (entry.called_at - entry.created_at).total_seconds()
                    wait_times.append(wait_time)
            
            if wait_times:
                avg_wait_time = sum(wait_times) / len(wait_times)
        
        # Priority breakdown
        priority_breakdown = {}
        for entry in base_query.all():
            priority = entry.priority_type
            if priority not in priority_breakdown:
                priority_breakdown[priority] = 0
            priority_breakdown[priority] += 1
        
        return {
            'date': report_date.isoformat(),
            'room_id': room_id,
            'total_patients': total_patients,
            'attended': attended,
            'absent': absent,
            'waiting': waiting,
            'called': called,
            'cancelled': cancelled,
            'average_wait_time_seconds': avg_wait_time,
            'priority_breakdown': priority_breakdown
        }
    
    @staticmethod
    def get_absence_report(start_date: Optional[date] = None, 
                          end_date: Optional[date] = None,
                          room_id: Optional[int] = None) -> dict:
        """
        Generate absence report.
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            room_id: Filter by room (optional)
            
        Returns:
            Absence report dict
        """
        if not start_date:
            start_date = date.today() - timedelta(days=7)
        if not end_date:
            end_date = date.today()
        
        query = AbsenceRecord.query.filter(
            func.date(AbsenceRecord.recorded_at) >= start_date,
            func.date(AbsenceRecord.recorded_at) <= end_date
        )
        
        if room_id:
            query = query.filter(AbsenceRecord.room_id == room_id)
        
        absences = query.all()
        
        # Group by date
        by_date = {}
        for absence in absences:
            date_key = absence.recorded_at.date().isoformat()
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(absence.to_dict())
        
        # Count by room
        by_room = {}
        for absence in absences:
            room_name = absence.room.name if absence.room else 'Unknown'
            if room_name not in by_room:
                by_room[room_name] = 0
            by_room[room_name] += 1
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_absences': len(absences),
            'by_date': by_date,
            'by_room': by_room
        }
    
    @staticmethod
    def get_room_performance(room_id: int, 
                            start_date: Optional[date] = None,
                            end_date: Optional[date] = None) -> dict:
        """
        Generate room performance report.
        
        Args:
            room_id: Room ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Performance metrics dict
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        room = Room.query.get(room_id)
        if not room:
            return {'error': 'Room not found'}
        
        query = QueueEntry.query.filter(
            QueueEntry.room_id == room_id,
            func.date(QueueEntry.created_at) >= start_date,
            func.date(QueueEntry.created_at) <= end_date
        )
        
        total = query.count()
        attended = query.filter(
            QueueEntry.status == CallStatus.ATTENDED.value
        ).count()
        absent = query.filter(
            QueueEntry.status == CallStatus.ABSENT.value
        ).count()
        
        # Calculate average calls per patient
        all_entries = query.all()
        avg_calls = 0
        if all_entries:
            total_calls = sum(e.call_count for e in all_entries)
            avg_calls = total_calls / len(all_entries)
        
        attendance_rate = (attended / total * 100) if total > 0 else 0
        absence_rate = (absent / total * 100) if total > 0 else 0
        
        return {
            'room_id': room_id,
            'room_name': room.name,
            'sector': room.sector,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_patients': total,
            'attended': attended,
            'absent': absent,
            'attendance_rate': round(attendance_rate, 2),
            'absence_rate': round(absence_rate, 2),
            'average_calls_per_patient': round(avg_calls, 2)
        }
    
    @staticmethod
    def get_hourly_distribution(report_date: Optional[date] = None,
                               room_id: Optional[int] = None) -> dict:
        """
        Get hourly distribution of patients.
        
        Args:
            report_date: Date for the report
            room_id: Filter by room (optional)
            
        Returns:
            Hourly distribution dict
        """
        if not report_date:
            report_date = date.today()
        
        query = QueueEntry.query.filter(
            func.date(QueueEntry.created_at) == report_date
        )
        
        if room_id:
            query = query.filter(QueueEntry.room_id == room_id)
        
        entries = query.all()
        
        distribution = {f"{h:02d}:00": 0 for h in range(24)}
        
        for entry in entries:
            hour_key = entry.created_at.strftime('%H:00')
            distribution[hour_key] += 1
        
        return {
            'date': report_date.isoformat(),
            'room_id': room_id,
            'hourly_distribution': distribution
        }
