from datetime import datetime, timezone
from typing import Optional

from src.domain.entities import Patient, PatientSensitivity, SensitivityHistory
from src.infrastructure.persistence.models import UserModel
from src.domain.exceptions import NotFoundError, ValidationError
from src.domain.interfaces.repositories import (
    IPatientRepository, IPatientSensitivityRepository,
    ISensitivityHistoryRepository, ISensitivityPresetRepository, IUserRepository,
)
from src.domain.value_objects import Sensitivity

class PatientService:
    def __init__(
        self,
        patient_repo: IPatientRepository,
        sensitivity_repo: IPatientSensitivityRepository,
        history_repo: ISensitivityHistoryRepository,
        preset_repo: ISensitivityPresetRepository,
        user_repo: IUserRepository,
    ):
        self._patient_repo = patient_repo
        self._sensitivity_repo = sensitivity_repo
        self._history_repo = history_repo
        self._preset_repo = preset_repo
        self.user_repo = user_repo

    def list_by_user(self, user_id: int, user_role: str = 'therapist') -> list:
        return self._patient_repo.find_by_user_id(user_id, user_role=user_role)

    def list_by_user_paginated(self, therapist_id: int, page: int = 1, per_page: int = 10, user_role: str = 'therapist') -> dict:
        return self._patient_repo.find_by_user_id_paginated(therapist_id, page, per_page, user_role=user_role)

    def get_by_id(self, patient_id: int) -> Patient:
        p = self._patient_repo.find_by_id(patient_id)
        if not p:
            raise NotFoundError('Paciente', patient_id)
        return p

    def create(self, therapist_id: int, name: str, lastname: str, document: str, email: str, password: str, birth_date=None, age: Optional[int] = None,
               diagnosis: Optional[str] = None, notes: Optional[str] = None) -> Patient:
        user = UserModel(name=name, lastname=lastname, email=email)
        user.set_password(password)
        user.role_id = 3
        user_save = self.user_repo.save(user)
        patient = Patient(therapist_id=therapist_id, user_id=user_save.id, name=name, lastname=lastname, document=document, birth_date=birth_date, age=age, diagnosis=diagnosis, notes=notes)
        return self._patient_repo.save(patient)

    def update(self, patient_id: int, data: dict) -> Patient:
        p = self.get_by_id(patient_id)
        for field in ('name', 'birth_date', 'age', 'diagnosis', 'notes'):
            if field in data:
                setattr(p, field, data[field])
        return self._patient_repo.save(p)

    def transfer(self, patient_id: int, new_user_id: int) -> Patient:
        p = self.get_by_id(patient_id)
        p.user_id = new_user_id
        return self._patient_repo.save(p)

    def delete(self, patient_id: int) -> None:
        self.get_by_id(patient_id)
        self._patient_repo.delete(patient_id)

    def get_sensitivity(self, patient_id: int):
        self.get_by_id(patient_id)
        ps = self._sensitivity_repo.find_by_patient_id(patient_id)
        preset_info = None
        if ps and ps.based_on_preset:
            preset = self._preset_repo.find_all()
            for p in preset:
                if p.id == ps.based_on_preset:
                    preset_info = {'id': p.id, 'name': p.name, 'difficulty_level': p.difficulty_level}
                    break
        return {
            'sensitivities': ps.sensitivities if ps else None,
            'calibration_data': ps.calibration_data if ps else None,
            'preset': preset_info,
            'updated_at': ps.updated_at.isoformat() if ps and ps.updated_at else None,
        }

    def update_sensitivity(self, patient_id: int, sensitivities: list,
                           preset_id: Optional[int] = None, reason: Optional[str] = None,
                           changed_by: Optional[int] = None,
                           calibration_data: Optional[list] = None) -> dict:
        self.get_by_id(patient_id)
        Sensitivity.from_list(sensitivities)

        ps = self._sensitivity_repo.find_by_patient_id(patient_id)
        old_sens = ps.sensitivities if ps else None

        history = SensitivityHistory(
            patient_id=patient_id,
            old_sensitivities=old_sens,
            new_sensitivities=sensitivities,
            reason=reason,
            changed_by=changed_by,
        )
        self._history_repo.save(history)

        if ps:
            ps.sensitivities = sensitivities
            ps.based_on_preset = preset_id
            ps.updated_at = datetime.now(timezone.utc)
            ps.updated_by = changed_by
            if calibration_data is not None:
                ps.calibration_data = calibration_data
        else:
            ps = PatientSensitivity(
                patient_id=patient_id,
                sensitivities=sensitivities,
                based_on_preset=preset_id,
                updated_by=changed_by,
            )
            if calibration_data is not None:
                ps.calibration_data = calibration_data
        saved = self._sensitivity_repo.save(ps)
        return {'sensitivities': saved.sensitivities, 'calibration_data': saved.calibration_data}

    def get_sensitivity_history(self, patient_id: int) -> list:
        self.get_by_id(patient_id)
        return self._history_repo.find_by_patient_id(patient_id)
