import { NgModule } from '@angular/core';
import { Routes, RouterModule, UrlSegment } from '@angular/router';
import { DownloadComponent } from './download/download.component';

function downloadMatcher(url: UrlSegment[]) {
  console.log('got url:', url);

  if (url.length < 3 || url[0].path !== 'download') {
    return null;
  }

  return {
    consumed: url,
    posParams: {
      url: url.slice(1)
    }
  };
}

const routes: Routes = [
  { path: 'download/:id', component: DownloadComponent,  }
  // { matcher: downloadMatcher, component: DownloadComponent,  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
