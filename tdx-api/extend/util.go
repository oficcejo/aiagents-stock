package extend

import (
	"bytes"
	"encoding/csv"
	"github.com/injoyai/conv"
	"io"
	"os"
	"path/filepath"
)

func toCsv(data [][]interface{}) (*bytes.Buffer, error) {
	buf := bytes.NewBuffer(nil)
	buf.WriteString("\xEF\xBB\xBF")
	w := csv.NewWriter(buf)
	for _, rows := range data {
		if err := w.Write(conv.Strings(rows)); err != nil {
			return nil, err
		}
	}
	w.Flush()
	return buf, nil
}

// newFile 新建文件,会覆盖
func newFile(filename string, v ...interface{}) error {
	if len(v) == 0 {
		return os.MkdirAll(filename, 0777)
	}
	dir, name := filepath.Split(filename)
	if len(dir) > 0 {
		if err := os.MkdirAll(dir, 0777); err != nil {
			return err
		}
	}
	if len(name) == 0 {
		return nil
	}
	f, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer f.Close()
	for _, k := range v {
		switch r := k.(type) {
		case nil:
		case io.Reader:
			if _, err = io.Copy(f, r); err != nil {
				return err
			}
		default:
			if _, err = f.Write(conv.Bytes(r)); err != nil {
				return err
			}
		}
	}
	return nil
}
