// compile with gcc `pkg-config --cflags gtk+-3.0` -o test test.c `pkg-config --libs gtk+-3.0`
#include <gtk/gtk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


struct pciDev {
  char bdf[256];
  int bus;
  int dev;
  int fun;

  char devStr[256];
  char venStr[256];
  char desc[256];
};

void parseLspci(struct pciDev *pDev, char *str);


static GtkTreeModel *
create_and_fill_model (void)
{
  GtkListStore  *store;
  GtkTreeIter    iter;
  store = gtk_list_store_new (4, G_TYPE_STRING, G_TYPE_STRING, G_TYPE_STRING, G_TYPE_STRING);
  //gtk_list_store_append (store, &iter);
  //gtk_list_store_set (store, &iter,
  //                    0, "BDF",
  //                    1, "Desc",
  //                    2, "VID",
  //                    3, "DID",
  //                    -1);
  FILE *fp;
  char path[1035];


  /* Open the command for reading. */
  fp = popen("lspci -mmnn", "r");
  if (fp == NULL) {
    printf("Failed to run command\n" );
    exit(1);
  }

  struct pciDev pDev;
  /* Read the output a line at a time. */
  while (fgets(path, sizeof(path)-1, fp) != NULL) {
    memset(&pDev.bdf,0,sizeof(pDev.bdf));
    memset(&pDev.devStr,0,sizeof(pDev.devStr));
    memset(&pDev.venStr,0,sizeof(pDev.venStr));
    memset(&pDev.desc,0,sizeof(pDev.desc));
    //printf("asdf: %s", path);
    parseLspci(&pDev,path);
    //printf("bus: %02x  dev: %02x fun: %02x\n",pDev.bus, pDev.dev, pDev.fun);
    //printf("dev: %s\n", pDev.devStr);
    //printf("ven: %s\n", pDev.venStr);
    //printf("desc: %s\n", pDev.desc);
    gtk_list_store_append (store, &iter);
    gtk_list_store_set (store, &iter,
                        0, pDev.bdf,
                        1, pDev.venStr,
                        2, pDev.devStr,
                        3, pDev.desc,
                        -1);
  }

  /* close */
  pclose(fp);
  return GTK_TREE_MODEL (store);
}

static GtkWidget *
create_view_and_model (void)
{
  GtkCellRenderer     *renderer;
  GtkTreeModel        *model;
  GtkWidget           *view;

  view = gtk_tree_view_new ();

  /* --- Column #1 --- */

  renderer = gtk_cell_renderer_text_new ();
  gtk_tree_view_insert_column_with_attributes (GTK_TREE_VIEW (view),
                                               -1,
                                               "BDF",
                                               renderer,
                                               "text", 0,
                                               NULL);

  /* --- Column #2 --- */

  renderer = gtk_cell_renderer_text_new ();
  gtk_tree_view_insert_column_with_attributes (GTK_TREE_VIEW (view),
                                               -1,
                                               "VID",
                                               renderer,
                                               "text", 1,
                                               NULL);

  /* --- Column #3 --- */

  renderer = gtk_cell_renderer_text_new ();
  gtk_tree_view_insert_column_with_attributes (GTK_TREE_VIEW (view),
                                               -1,
                                               "DID",
                                               renderer,
                                               "text", 2,
                                               NULL);
  /* --- Column #4 --- */

  renderer = gtk_cell_renderer_text_new ();
  gtk_tree_view_insert_column_with_attributes (GTK_TREE_VIEW (view),
                                               -1,
                                               "Desc",
                                               renderer,
                                               "text", 3,
                                               NULL);
  model = create_and_fill_model ();

  gtk_tree_view_set_model (GTK_TREE_VIEW (view), model);

  /* The tree view has acquired its own reference to the
   *  model, so we can drop ours. That way the model will
   *  be freed automatically when the tree view is destroyed */

  g_object_unref (model);

  return view;
}

static void
activate (GtkApplication* app,
          gpointer        user_data)
{
  GtkWidget *window;
  GtkWidget *view;

  window = gtk_application_window_new (app);
  gtk_window_set_title (GTK_WINDOW (window), "Window");
  gtk_window_set_default_size (GTK_WINDOW (window), 200, 200);

  view = create_view_and_model ();

  gtk_container_add (GTK_CONTAINER (window), view);

  gtk_widget_show_all (window);

}

int
main (int    argc,
      char **argv)
{
  GtkApplication *app;
  int status;

  app = gtk_application_new ("org.gtk.example", G_APPLICATION_FLAGS_NONE);
  g_signal_connect (app, "activate", G_CALLBACK (activate), NULL);
  status = g_application_run (G_APPLICATION (app), argc, argv);
  g_object_unref (app);

  return status;
}

void parseLspci(struct pciDev *pDev, char *str)
{
  char *p ;

  int c;
  int i=0;
  int firstSpace;

  // find first space - will be after BDF column
  for( p=str, i=0; *p!='\0'; p++, i++ )
  {
    c = (unsigned char) *p ;
    if( isspace(c) )
    {
      firstSpace = i;
      break;
    }
  }

  // create bdf string, then parse that for bus, dev, fun
  char bdf[256];
  strncpy(bdf,str,firstSpace);
  strncpy(pDev->bdf,str,firstSpace);

  char *b ;
  b = strtok(bdf,":");
  pDev->bus = (int)strtol(b, NULL, 16);
  b = strtok(NULL,".");
  pDev->dev = (int)strtol(b, NULL, 16);
  b = strtok(NULL,".");
  pDev->fun = (int)strtol(b, NULL, 16);

  // now parse rest of string for device, vendor, desc info
  int head=0, tail=0;
  //printf("str: %s\n",str+firstSpace);
  for( p=str+firstSpace, i=firstSpace; *p!='\0'; p++, i++ )
  {
    c = (unsigned char) *p ;
    if(head==0 && c=='\"')
    {
      head=i+1;
    }
    else if(tail==0 && c=='\"')
    {
      strncpy(pDev->devStr,str+head,i-head);
      break;
    }
  }

  head=0;
  tail=0;
  p++; i++;
  //printf("ven: %s\n",p);
  for(; *p!='\0'; p++, i++ )
  {
    c = (unsigned char) *p ;
    if(head==0 && c=='\"')
    {
      head=i+1;
    }
    else if(tail==0 && c=='\"')
    {
      strncpy(pDev->venStr,str+head,i-head);
      break;
    }
  }

  head=0;
  tail=0;
  p++; i++;
  //printf("desc: %s\n",p);
  for(; *p!='\0'; p++, i++ )
  {
    c = (unsigned char) *p ;
    if(head==0 && c=='\"')
    {
      head=i+1;
    }
    else if(tail==0 && c=='\"')
    {
      strncpy(pDev->desc,str+head,i-head);
      break;
    }
  }
}
