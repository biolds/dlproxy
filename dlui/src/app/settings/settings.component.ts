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
    ca_key: [''],
    certs_key: ['']
  });

  certLoading = false;

  constructor(
    private settingsService: SettingsService,
    private fb: FormBuilder) {
  }

  getSettings(): void {
    this.settingsService.getSettings()
      .subscribe(settings => {this.settingsForm.patchValue(settings)});
  }

  certificateDownload(): void {
    window.location.pathname = `/cacert_download`;
  }

  generateNew() {
    this.certLoading = true;
    this.settingsService.generateNewCerts()
      .subscribe(settings => {
        this.settingsForm.patchValue(settings);
        this.certLoading = false;
      });
  }

  onSubmit() {
    this.settingsService.setSettings(this.settingsForm.value)
      .subscribe(settings => {this.settingsForm.patchValue(settings)});
  }

  ngOnInit() {
    this.getSettings();
  }
}
