import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Settings } from '../settings';
import { SettingsService } from '../settings.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {
  settingsForm = this.fb.group({
    ca_cert: [''],
    ca_key: ['']
  });

  constructor(
    private settingsService: SettingsService,
    private fb: FormBuilder) {
  }

  generateNew() {
    this.settingsService.generateNewCerts()
      .subscribe(settings => {this.settingsForm.patchValue(settings)});
  }

  onSubmit() {
    console.log('got:', this.settingsForm.value);
  }

  getSettings(): void {
    this.settingsService.getSettings()
      .subscribe(settings => {this.settingsForm.patchValue(settings)});
  }

  ngOnInit() {
    this.getSettings();
  }
}
