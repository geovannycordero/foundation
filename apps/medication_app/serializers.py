"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from rest_framework import serializers

from emr.models import Medication, MedicationTextNote, MedicationPinToProblem
from users_app.serializers import SafeUserSerializer


class MedicationTextNoteSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = MedicationTextNote
        fields = (
            'id',
            'author',
            'note',
            'medication',
            'datetime',
        )


class MedicationSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    patient = SafeUserSerializer()
    medication_notes = MedicationTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Medication

        fields = (
            'id',
            'author',
            'patient',
            'medication_notes',
            'name',
            'concept_id',
            'current',
            'search_str',
            'created_on',
        )


class MedicationPinToProblemSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    medication = MedicationSerializer()

    class Meta:
        model = MedicationPinToProblem
        fields = (
            'id',
            'author',
            'medication',
            'problem',
        )
