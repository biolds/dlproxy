import { Url } from './url';

export class Download {
  id: number;
  url: Url;
  date: string;
  filesize: number;
  filename: string;
  mimetype: string;
  current_size: number;
  to_keep: boolean;
  downloaded: boolean;
}
