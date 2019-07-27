import { Url } from './url';

export class Download {
  id: number;
  url: Url;
  date: number;
  filesize: number;
  filename: string;
  mimetype: string;
  current_size: number;
  to_keep: boolean;
  downloaded: boolean;
  bandwidth: number;
  stats_date: number;
}
