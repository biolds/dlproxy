import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDatepickerModule } from '@angular/material/datepicker'; 
import { MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material';
import { MatMomentDateModule } from '@angular/material-moment-adapter';

import { ErrorComponent } from './error/error.component';
import { MaintabsComponent } from './maintabs/maintabs.component';
import { SettingsComponent } from './settings/settings.component';
import { DownloadComponent, DownloadCancelDialog } from './download/download.component';
import { DownloadsComponent } from './downloads/downloads.component';
import { HistoryComponent } from './history/history.component';
import { UrlComponent } from './url/url.component';
import { SearchComponent } from './search/search.component';
import { SearchLogComponent } from './search-log/search-log.component';
import { HistoryLogComponent } from './history-log/history-log.component';

@NgModule({
  declarations: [
    AppComponent,
    DownloadComponent,
    DownloadCancelDialog,
    ErrorComponent,
    MaintabsComponent,
    SettingsComponent,
    DownloadsComponent,
    HistoryComponent,
    UrlComponent,
    SearchComponent,
    SearchLogComponent,
    HistoryLogComponent
  ],
  entryComponents: [
    DownloadCancelDialog
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    ReactiveFormsModule,
    BrowserAnimationsModule,
    MatToolbarModule,
    MatGridListModule,
    MatIconModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatDatepickerModule,
    MatDialogModule,
    MatExpansionModule,
    MatListModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTabsModule,
    MatFormFieldModule,
    MatMomentDateModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
